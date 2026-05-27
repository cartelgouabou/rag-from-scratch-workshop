from __future__ import annotations

import asyncio

from agent.llm_client import VercelAIGatewayClient


class GatewayEmbedder:
    def __init__(
        self,
        gateway_client: VercelAIGatewayClient,
        model_name: str,
        *,
        batch_size: int = 8,
        batch_delay_seconds: float = 2.0,
    ) -> None:
        self.gateway_client = gateway_client
        self.model_name = model_name
        self.batch_size = max(batch_size, 1)
        self.batch_delay_seconds = max(batch_delay_seconds, 0.0)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            if start > 0 and self.batch_delay_seconds > 0:
                await asyncio.sleep(self.batch_delay_seconds)
            batch = texts[start : start + self.batch_size]
            embeddings.extend(
                await self.gateway_client.embed_texts(model=self.model_name, inputs=batch)
            )
        return embeddings

    async def embed_query(self, query: str) -> list[float]:
        return (await self.embed_texts([query]))[0]
