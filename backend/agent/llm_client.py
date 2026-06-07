from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, AsyncIterator

import httpx


class VercelAIGatewayClient:
    _base_retry_delay_seconds = 2.0

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        max_retries: int = 5,
        max_retry_delay_seconds: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._max_retries = max_retries
        self._max_retry_delay_seconds = max_retry_delay_seconds
        self._client = httpx.AsyncClient(timeout=90.0)

    @property
    def is_configured(self) -> bool:
        normalized = self.api_key.strip().lower()
        return bool(normalized) and normalized not in {"replace_me", "changeme", "your_key_here"}

    async def complete(
        self,
        *,
        model: str,
        system: str,
        user: str,
        temperature: float = 0,
        max_tokens: int = 256,
    ) -> str:
        response = await self._post_with_retry(
            f"{self.base_url}/chat/completions",
            json_body={
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "providerOptions": self._provider_options,
            },
        )
        payload = response.json()
        return payload["choices"][0]["message"]["content"]

    async def stream_chat(
        self,
        *,
        model: str,
        system: str,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 700,
    ) -> AsyncIterator[str]:
        for attempt in range(self._max_retries + 1):
            async with self._client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self._headers,
                json={
                    "model": model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                    "messages": [{"role": "system", "content": system}, *messages],
                    "providerOptions": self._provider_options,
                },
            ) as response:
                if response.is_error:
                    body = await response.aread()
                    decoded_body = body.decode("utf-8", errors="replace")
                    error = self._build_http_status_error(response, decoded_body)
                    if self._should_retry(error, attempt):
                        delay = self._retry_delay_seconds(response, attempt)
                        await asyncio.sleep(delay)
                        continue
                    raise error

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line.removeprefix("data:").strip()
                    if data == "[DONE]":
                        break
                    payload = json.loads(data)
                    delta = payload["choices"][0].get("delta", {})
                    content = delta.get("content")
                    if isinstance(content, str) and content:
                        yield content
                return

        raise RuntimeError("Streaming request exhausted retries without a successful response.")

    async def embed_texts(self, *, model: str, inputs: list[str]) -> list[list[float]]:
        if not inputs:
            return []

        response = await self._post_with_retry(
            f"{self.base_url}/embeddings",
            json_body={
                "model": model,
                "input": inputs,
                "providerOptions": self._provider_options,
            },
            operation="embeddings",
        )
        payload = response.json()
        return [item["embedding"] for item in payload["data"]]

    async def close(self) -> None:
        await self._client.aclose()

    @property
    def _headers(self) -> dict[str, str]:
        if not self.is_configured:
            raise RuntimeError("VERCEL_AI_GATEWAY_KEY is not configured.")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @property
    def _provider_options(self) -> dict[str, dict[str, bool]]:
        return {
            "gateway": {
                "zeroDataRetention": True,
            }
        }

    async def _post_with_retry(
        self,
        url: str,
        *,
        json_body: dict[str, Any],
        operation: str = "post",
    ) -> httpx.Response:
        last_error: httpx.HTTPStatusError | None = None
        for attempt in range(self._max_retries + 1):
            response = await self._client.post(
                url,
                headers=self._headers,
                json=json_body,
            )
            if not response.is_error:
                return response

            error = self._build_http_status_error(response, response.text)
            last_error = error
            if not self._should_retry(error, attempt):
                raise error

            delay = self._retry_delay_seconds(response, attempt)
            await asyncio.sleep(delay)

        if last_error is not None:
            raise last_error
        raise RuntimeError("Gateway request exhausted retries without a response.")

    def _should_retry(self, error: httpx.HTTPStatusError, attempt: int) -> bool:
        return error.response.status_code == 429 and attempt < self._max_retries

    def _retry_delay_seconds(self, response: httpx.Response, attempt: int) -> float:
        retry_after_ms = response.headers.get("retry-after-ms")
        if retry_after_ms:
            try:
                seconds = float(retry_after_ms) / 1000.0
                if 0 < seconds <= 120:
                    return min(seconds, self._max_retry_delay_seconds)
            except ValueError:
                pass

        retry_after = response.headers.get("retry-after")
        if retry_after:
            try:
                seconds = float(retry_after)
                if 0 < seconds <= 120:
                    return min(seconds, self._max_retry_delay_seconds)
            except ValueError:
                try:
                    retry_datetime = parsedate_to_datetime(retry_after)
                    if retry_datetime.tzinfo is None:
                        retry_datetime = retry_datetime.replace(tzinfo=timezone.utc)
                    seconds = (retry_datetime - datetime.now(timezone.utc)).total_seconds()
                    if 0 < seconds <= 120:
                        return min(seconds, self._max_retry_delay_seconds)
                except (TypeError, ValueError):
                    pass

        delay = min(self._base_retry_delay_seconds * (2**attempt), self._max_retry_delay_seconds)
        if response.status_code == 429 and "free tier" in response.text.lower():
            delay = max(20.0, delay)
        return delay

    def _build_http_status_error(self, response: httpx.Response, body: str) -> httpx.HTTPStatusError:
        request = response.request
        trimmed_body = body[:500]
        message = (
            f"Gateway request failed with status {response.status_code} for {request.method} {request.url}. "
            f"Response body: {trimmed_body}"
        )
        return httpx.HTTPStatusError(message, request=request, response=response)
