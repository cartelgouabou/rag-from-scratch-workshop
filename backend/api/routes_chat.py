from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, AsyncIterator

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from agent.router import RouteDecision, RoutingSource, route_question
from schemas import ChatRequest

router = APIRouter()

SQL_PROMPT = """
Tu traduis une question métier en SQL SQLite.
Réponds uniquement avec une requête SQL SELECT valide, sans markdown, sans explication.
Utilise uniquement les tables et colonnes disponibles dans le schéma fourni.
Le schéma liste des couples "Document" / "Table": si la question mentionne un nom de fichier, utilise la table correspondante.
Si la question demande combien de lignes contient un fichier tabulaire, réponds avec COUNT(*).
Si la question ne peut pas être résolue avec le schéma, retourne:
SELECT 'INSUFFICIENT_DATA' AS error
""".strip()

VECTOR_PROMPT = """
Tu es un assistant RAG. Réponds en français en utilisant uniquement le contexte fourni.
Si le contexte est insuffisant, dis clairement que tu ne sais pas encore répondre avec les documents disponibles.
Sois précis, pédagogue et synthétique.
""".strip()

SQL_ANSWER_PROMPT = """
Tu es un assistant de restitution.
Tu reçois une question utilisateur, une requête SQL et le résultat tabulaire.
Réponds en français de façon claire et concise.
Si aucune ligne ne correspond, explique-le explicitement.
""".strip()

BOTH_ANSWER_PROMPT = """
Tu es un assistant RAG qui combine deux sources:
1. un résultat SQL structuré
2. un contexte documentaire vectoriel.

Utilise le résultat SQL pour les faits exacts, chiffres et dénombrements.
Utilise le contexte documentaire pour les éléments narratifs, postes, profils, résumés et formulations.
Si une des deux sources est insuffisante, dis-le clairement sans inventer.
Réponds en français, de façon concise et utile.
""".strip()

STOPWORDS = {
    "alors",
    "avec",
    "dans",
    "des",
    "du",
    "est",
    "les",
    "pas",
    "pour",
    "quel",
    "quelle",
    "quels",
    "quelles",
    "sont",
    "sur",
    "une",
    "who",
    "what",
    "when",
    "where",
    "which",
}


@dataclass
class SQLExecutionResult:
    sql_query: str
    preview_rows: list[dict[str, Any]]
    sources: list[dict[str, str]]


@dataclass
class VectorRetrievalResult:
    results: list[dict[str, Any]]
    sources: list[dict[str, str]]
    combined_context: str


@router.post("")
async def chat(request: Request, payload: ChatRequest) -> StreamingResponse:
    settings = request.app.state.settings
    sql_store = request.app.state.sql_store
    vector_store = request.app.state.vector_store
    embedder = request.app.state.embedder
    gateway_client = request.app.state.gateway_client

    async def event_stream() -> AsyncIterator[str]:
        documents = sql_store.list_documents()
        active_chunk_counts = vector_store.get_document_chunk_counts()
        decision = await route_question(
            gateway_client,
            settings.router_model,
            payload.message,
            sql_inventory=sql_store.build_schema_context(min(settings.sql_preview_rows, 2)),
            document_inventory=_build_document_inventory(documents, active_chunk_counts),
        )
        yield _sse(
            {
                "type": "routing",
                "decision": decision.route,
                "confidence": decision.confidence,
                "reason": decision.reason,
            }
        )

        if not gateway_client.is_configured:
            warning = (
                "Le chat nécessite une clé Vercel AI Gateway valide. "
                "L'ingestion est disponible, mais la génération de réponses est désactivée."
            )
            yield _sse({"type": "token", "content": warning})
            yield _sse({"type": "done", "source": decision.route, "chunks_used": 0, "sources": []})
            return

        if decision.route == "sql":
            async for event in _stream_sql_answer(
                gateway_client=gateway_client,
                answer_model=settings.answer_model,
                sql_store=sql_store,
                preview_rows=settings.sql_preview_rows,
                payload=payload,
            ):
                yield event
            return

        if decision.route == "vector":
            async for event in _stream_vector_answer(
                gateway_client=gateway_client,
                settings=settings,
                vector_store=vector_store,
                embedder=embedder,
                payload=payload,
                documents=documents,
            ):
                yield event
            return

        async for event in _stream_both_answer(
            gateway_client=gateway_client,
            settings=settings,
            sql_store=sql_store,
            vector_store=vector_store,
            embedder=embedder,
            payload=payload,
            documents=documents,
            decision=decision,
        ):
            yield event

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


async def _stream_sql_answer(
    *,
    gateway_client: Any,
    answer_model: str,
    sql_store: Any,
    preview_rows: int,
    payload: ChatRequest,
) -> AsyncIterator[str]:
    try:
        sql_result = await _prepare_sql_context(
            gateway_client=gateway_client,
            answer_model=answer_model,
            sql_store=sql_store,
            preview_rows=preview_rows,
            payload=payload,
        )
        answer_message = {
            "role": "user",
            "content": (
                f"Historique:\n{_format_history(payload.history)}\n\n"
                f"Question: {payload.message}\n"
                f"Requête SQL: {sql_result.sql_query}\n"
                f"Résultat: {json.dumps(sql_result.preview_rows, ensure_ascii=False, default=str)}"
            ),
        }
        async for token in gateway_client.stream_chat(
            model=answer_model,
            system=SQL_ANSWER_PROMPT,
            messages=[answer_message],
            temperature=0.1,
            max_tokens=500,
        ):
            yield _sse({"type": "token", "content": token})
        yield _sse({"type": "done", "source": "sql", "chunks_used": 0, "sources": sql_result.sources})
    except Exception as exc:
        fallback = f"Je n'ai pas réussi à interroger les données tabulaires: {_friendly_error(exc)}"
        yield _sse({"type": "token", "content": fallback})
        yield _sse({"type": "done", "source": "sql", "chunks_used": 0, "sources": []})


async def _stream_vector_answer(
    *,
    gateway_client: Any,
    settings: Any,
    vector_store: Any,
    embedder: Any,
    payload: ChatRequest,
    documents: list[dict[str, Any]],
) -> AsyncIterator[str]:
    try:
        vector_result = await _prepare_vector_context(
            settings=settings,
            vector_store=vector_store,
            embedder=embedder,
            payload=payload,
            documents=documents,
        )
        if vector_result is None:
            yield _sse(
                {
                    "type": "token",
                    "content": "Aucun document pertinent n'a encore été indexé pour répondre à cette question.",
                }
            )
            yield _sse({"type": "done", "source": "vector", "chunks_used": 0, "sources": []})
            return

        answer_message = {
            "role": "user",
            "content": (
                f"Historique:\n{_format_history(payload.history)}\n\n"
                f"Question: {payload.message}\n\n"
                f"Contexte:\n{vector_result.combined_context}"
            ),
        }
        async for token in gateway_client.stream_chat(
            model=settings.answer_model,
            system=VECTOR_PROMPT,
            messages=[answer_message],
            temperature=0.2,
            max_tokens=700,
        ):
            yield _sse({"type": "token", "content": token})
        yield _sse(
            {
                "type": "done",
                "source": "vector",
                "chunks_used": len(vector_result.results),
                "sources": vector_result.sources,
            }
        )
    except Exception as exc:
        yield _sse(
            {
                "type": "token",
                "content": f"Je n'ai pas réussi à générer une réponse à partir des documents: {_friendly_error(exc)}",
            }
        )
        yield _sse({"type": "done", "source": "vector", "chunks_used": 0, "sources": []})


async def _stream_both_answer(
    *,
    gateway_client: Any,
    settings: Any,
    sql_store: Any,
    vector_store: Any,
    embedder: Any,
    payload: ChatRequest,
    documents: list[dict[str, Any]],
    decision: RouteDecision,
) -> AsyncIterator[str]:
    sql_result: SQLExecutionResult | None = None
    vector_result: VectorRetrievalResult | None = None
    sql_error: Exception | None = None
    vector_error: Exception | None = None

    try:
        sql_result = await _prepare_sql_context(
            gateway_client=gateway_client,
            answer_model=settings.answer_model,
            sql_store=sql_store,
            preview_rows=settings.sql_preview_rows,
            payload=payload,
        )
    except Exception as exc:
        sql_error = exc

    try:
        vector_result = await _prepare_vector_context(
            settings=settings,
            vector_store=vector_store,
            embedder=embedder,
            payload=payload,
            documents=documents,
        )
    except Exception as exc:
        vector_error = exc

    if sql_result and vector_result:
        combined_sources = sql_result.sources + vector_result.sources
        answer_message = {
            "role": "user",
            "content": (
                f"Historique:\n{_format_history(payload.history)}\n\n"
                f"Question: {payload.message}\n\n"
                f"Bloc SQL:\nRequête: {sql_result.sql_query}\n"
                f"Résultat: {json.dumps(sql_result.preview_rows, ensure_ascii=False, default=str)}\n\n"
                f"Bloc documentaire:\n{vector_result.combined_context}"
            ),
        }
        try:
            async for token in gateway_client.stream_chat(
                model=settings.answer_model,
                system=BOTH_ANSWER_PROMPT,
                messages=[answer_message],
                temperature=0.15,
                max_tokens=700,
            ):
                yield _sse({"type": "token", "content": token})
            yield _sse(
                {
                    "type": "done",
                    "source": "both",
                    "chunks_used": len(vector_result.results),
                    "sources": combined_sources,
                }
            )
            return
        except Exception as exc:
            sql_error = sql_error or exc

    for fallback_route in decision.fallback_order:
        if fallback_route == "sql" and sql_result:
            async for event in _stream_sql_from_result(
                gateway_client=gateway_client,
                answer_model=settings.answer_model,
                payload=payload,
                sql_result=sql_result,
            ):
                yield event
            return
        if fallback_route == "vector" and vector_result:
            async for event in _stream_vector_from_result(
                gateway_client=gateway_client,
                answer_model=settings.answer_model,
                payload=payload,
                vector_result=vector_result,
            ):
                yield event
            return

    errors = [error for error in [sql_error, vector_error] if error is not None]
    if errors:
        fallback = " ; ".join(_friendly_error(error) for error in errors)
    else:
        fallback = "les branches SQL et vectorielle n'ont pas retourne de contexte exploitable"
    yield _sse({"type": "token", "content": f"Je n'ai pas réussi à combiner les deux sources: {fallback}"})
    yield _sse({"type": "done", "source": "both", "chunks_used": 0, "sources": []})


async def _stream_sql_from_result(
    *,
    gateway_client: Any,
    answer_model: str,
    payload: ChatRequest,
    sql_result: SQLExecutionResult,
) -> AsyncIterator[str]:
    answer_message = {
        "role": "user",
        "content": (
            f"Historique:\n{_format_history(payload.history)}\n\n"
            f"Question: {payload.message}\n"
            f"Requête SQL: {sql_result.sql_query}\n"
            f"Résultat: {json.dumps(sql_result.preview_rows, ensure_ascii=False, default=str)}"
        ),
    }
    async for token in gateway_client.stream_chat(
        model=answer_model,
        system=SQL_ANSWER_PROMPT,
        messages=[answer_message],
        temperature=0.1,
        max_tokens=500,
    ):
        yield _sse({"type": "token", "content": token})
    yield _sse({"type": "done", "source": "sql", "chunks_used": 0, "sources": sql_result.sources})


async def _stream_vector_from_result(
    *,
    gateway_client: Any,
    answer_model: str,
    payload: ChatRequest,
    vector_result: VectorRetrievalResult,
) -> AsyncIterator[str]:
    answer_message = {
        "role": "user",
        "content": (
            f"Historique:\n{_format_history(payload.history)}\n\n"
            f"Question: {payload.message}\n\n"
            f"Contexte:\n{vector_result.combined_context}"
        ),
    }
    async for token in gateway_client.stream_chat(
        model=answer_model,
        system=VECTOR_PROMPT,
        messages=[answer_message],
        temperature=0.2,
        max_tokens=700,
    ):
        yield _sse({"type": "token", "content": token})
    yield _sse(
        {
            "type": "done",
            "source": "vector",
            "chunks_used": len(vector_result.results),
            "sources": vector_result.sources,
        }
    )


async def _prepare_sql_context(
    *,
    gateway_client: Any,
    answer_model: str,
    sql_store: Any,
    preview_rows: int,
    payload: ChatRequest,
) -> SQLExecutionResult:
    schema_context = sql_store.build_schema_context(preview_rows)
    sql_query = await gateway_client.complete(
        model=answer_model,
        system=SQL_PROMPT,
        user=(
            f"Schema:\n{schema_context}\n\n"
            f"Question: {payload.message}\n"
            "SQL:"
        ),
        max_tokens=300,
        temperature=0,
    )
    sql_query = _strip_code_fences(sql_query)
    rows = sql_store.execute_query(sql_query)
    return SQLExecutionResult(
        sql_query=sql_query,
        preview_rows=rows[:20],
        sources=_extract_sql_sources(sql_store, sql_query),
    )


async def _prepare_vector_context(
    *,
    settings: Any,
    vector_store: Any,
    embedder: Any,
    payload: ChatRequest,
    documents: list[dict[str, Any]],
) -> VectorRetrievalResult | None:
    query_embedding = await embedder.embed_query(payload.message)
    filename_filter = _extract_filename_filter(payload.message, documents)
    candidate_count = max(settings.vector_top_k * 3, settings.vector_top_k)

    candidates: list[dict[str, Any]] = []
    if filename_filter:
        candidates.extend(
            vector_store.query(
                query_embedding,
                candidate_count,
                where={"filename": filename_filter},
            )
        )
    candidates.extend(vector_store.query(query_embedding, candidate_count))

    unique_candidates = _deduplicate_results(candidates)
    if not unique_candidates:
        return None

    reranked = _rerank_candidates(
        payload.message,
        unique_candidates,
        filename_filter=filename_filter,
    )
    selected_results = _diversify_results(reranked, top_k=settings.vector_top_k, max_per_document=3)
    if not selected_results:
        return None

    context_blocks = []
    for index, item in enumerate(selected_results, start=1):
        metadata = item["metadata"] or {}
        section_title = metadata.get("section_title")
        heading = metadata.get("filename", "unknown")
        if isinstance(section_title, str) and section_title:
            heading = f"{heading} [{section_title}]"
        context_blocks.append(f"Source {index}: {heading}\n{item['content']}")

    return VectorRetrievalResult(
        results=selected_results,
        sources=_build_vector_sources(selected_results),
        combined_context="\n\n".join(context_blocks),
    )


def _build_document_inventory(
    documents: list[dict[str, Any]],
    active_chunk_counts: dict[str, int],
) -> str:
    if not documents:
        return "Aucun document disponible."

    sections: list[str] = []
    for document in documents:
        sections.append(
            "- "
            + f"{document['filename']} | type={document['type']} | active_chunks={active_chunk_counts.get(document['id'], 0)}"
        )
    return "\n".join(sections)


def _extract_filename_filter(question: str, documents: list[dict[str, Any]]) -> str | None:
    normalized_question = _normalize_text(question)
    for document in documents:
        filename = str(document.get("filename", ""))
        if not filename:
            continue
        normalized_filename = _normalize_text(filename)
        stem = _normalize_text(filename.rsplit(".", 1)[0])
        if normalized_filename and normalized_filename in normalized_question:
            return filename
        if stem and stem in normalized_question:
            return filename
    return None


def _deduplicate_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, Any]] = set()
    for item in results:
        metadata = item.get("metadata") or {}
        key = (
            str(metadata.get("document_id", "")),
            metadata.get("chunk_index"),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _rerank_candidates(
    question: str,
    results: list[dict[str, Any]],
    *,
    filename_filter: str | None,
) -> list[dict[str, Any]]:
    query_tokens = _extract_query_tokens(question)
    normalized_question = _normalize_text(question)
    scored_results: list[dict[str, Any]] = []

    for item in results:
        metadata = item.get("metadata") or {}
        content = str(item.get("content", ""))
        normalized_content = _normalize_text(content)
        normalized_filename = _normalize_text(str(metadata.get("filename", "")))
        content_tokens = set(normalized_content.split())
        filename_tokens = set(normalized_filename.split())
        distance = item.get("distance")
        similarity = 1.0 / (1.0 + max(float(distance), 0.0)) if isinstance(distance, (int, float)) else 0.0

        content_overlap = len(query_tokens & content_tokens)
        filename_overlap = len(query_tokens & filename_tokens)
        score = similarity
        score += min(content_overlap, 5) * 0.08
        score += min(filename_overlap, 3) * 0.14

        if filename_filter and metadata.get("filename") == filename_filter:
            score += 0.35
        if normalized_question and normalized_question in normalized_content:
            score += 0.18

        scored_results.append({**item, "score": score})

    return sorted(scored_results, key=lambda item: float(item.get("score", 0.0)), reverse=True)


def _diversify_results(
    results: list[dict[str, Any]],
    *,
    top_k: int,
    max_per_document: int,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    per_document: dict[str, int] = {}

    for item in results:
        metadata = item.get("metadata") or {}
        document_id = str(metadata.get("document_id", ""))
        current_count = per_document.get(document_id, 0)
        if current_count >= max_per_document:
            continue
        selected.append(item)
        per_document[document_id] = current_count + 1
        if len(selected) >= top_k:
            break
    return selected


def _extract_query_tokens(question: str) -> set[str]:
    return {
        token
        for token in _normalize_text(question).split()
        if len(token) > 2 and token not in STOPWORDS
    }


def _friendly_error(error: Exception) -> str:
    if isinstance(error, httpx.HTTPStatusError):
        body = error.response.text.lower()
        if error.response.status_code == 429:
            return "la limite de requêtes Vercel AI Gateway a été atteinte"
        if "zero data retention" in body or "zdr" in body:
            return "la contrainte zero data retention demandee n'est pas disponible pour ce modele, ce plan ou ce provider"
        if error.response.status_code == 403:
            return "le modele Vercel configure n'est pas accessible avec le plan, les credits ou les contraintes zero data retention actuels"
    return str(error)


def _format_history(history: list) -> str:
    if not history:
        return "Aucun historique."
    return "\n".join(f"{item.role}: {item.content}" for item in history)


def _extract_sql_sources(sql_store: Any, sql_query: str) -> list[dict[str, str]]:
    lowered_query = sql_query.lower()
    sources: list[dict[str, str]] = []
    for document in sql_store.list_documents():
        table_name = document.get("sql_table_name")
        if not isinstance(table_name, str) or not table_name:
            continue
        if table_name.lower() not in lowered_query:
            continue
        sources.append(
            {
                "title": str(document.get("filename", "Table SQL")),
                "detail": f"table {table_name}",
                "origin": "sql",
            }
        )
    return sources


def _build_vector_sources(results: list[dict[str, Any]]) -> list[dict[str, str]]:
    sources: list[dict[str, str]] = []
    for item in results:
        metadata = item.get("metadata") or {}
        detail_parts: list[str] = []

        page_number = metadata.get("page_number")
        row_number = metadata.get("row_number")
        sheet_name = metadata.get("sheet_name")
        source_modality = metadata.get("source_modality")
        extraction_source = metadata.get("extraction_source")
        section_title = metadata.get("section_title")

        if isinstance(page_number, int):
            detail_parts.append(f"page {page_number}")
        if isinstance(row_number, int):
            detail_parts.append(f"ligne {row_number}")
        if isinstance(sheet_name, str) and sheet_name:
            detail_parts.append(sheet_name)
        if isinstance(section_title, str) and section_title:
            detail_parts.append(section_title)
        if isinstance(source_modality, str) and source_modality:
            detail_parts.append(source_modality)
        if isinstance(extraction_source, str) and extraction_source:
            detail_parts.append(extraction_source)

        source = {
            "title": str(metadata.get("filename", "Document")),
            "detail": " • ".join(detail_parts) if detail_parts else "chunk vectoriel",
            "excerpt": _build_excerpt(str(item.get("content", ""))),
            "origin": "vector",
        }
        if source not in sources:
            sources.append(source)
    return sources


def _build_excerpt(content: str, max_length: int = 180) -> str:
    normalized = " ".join(content.split())
    if len(normalized) <= max_length:
        return normalized
    return normalized[: max_length - 3].rstrip() + "..."


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", ascii_value.lower()).strip()


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _strip_code_fences(content: str) -> str:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.removeprefix("sql").strip()
    return cleaned.strip()
