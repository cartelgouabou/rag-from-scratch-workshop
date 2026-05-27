from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import HTTPException

from ingestion.chunker import TextChunker
from ingestion.loader import (
    ExtractedDocument,
    SupportedFileType,
    TextUnit,
    dataframe_to_text_rows,
    detect_file_type,
    extract_image_document,
    extract_pdf_document,
    load_csv,
    load_excel,
)


@dataclass
class IngestionResult:
    document_id: str
    filename: str
    file_type: SupportedFileType
    nb_chunks: int
    nb_records: int
    duration_ms: int


async def ingest_document_bytes(
    *,
    settings: Any,
    sql_store: Any,
    vector_store: Any,
    embedder: Any,
    source_store: Any,
    document_id: str,
    filename: str,
    content: bytes,
    existing_document: dict[str, Any] | None = None,
) -> IngestionResult:
    started_at = time.perf_counter()
    max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_size_bytes:
        raise HTTPException(status_code=413, detail="Uploaded file is too large.")
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    try:
        file_type = detect_file_type(filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    source_path = source_store.save(document_id, filename, content)
    chunker = TextChunker(settings.chunk_size, settings.chunk_overlap)
    sql_table_name: str | None = None
    previous_table_name = None if existing_document is None else existing_document.get("sql_table_name")

    try:
        extracted, nb_records, dataframe = _extract_document(
            file_type=file_type,
            filename=filename,
            content=content,
            ocr_dpi=settings.ocr_dpi,
        )
        chunk_payloads = _chunk_text_units(chunker, extracted.units, file_type=file_type)
        if not chunk_payloads:
            raise HTTPException(status_code=400, detail="The uploaded file does not contain usable content.")

        chunk_texts = [payload["text"] for payload in chunk_payloads]
        chunk_metadatas = [payload["metadata"] for payload in chunk_payloads]
        embeddings = await embedder.embed_texts(chunk_texts)

        if previous_table_name:
            sql_store.drop_table_if_exists(previous_table_name)
        if existing_document is not None:
            vector_store.delete_document(document_id)

        if dataframe is not None:
            sql_table_name = sql_store.create_tabular_table(document_id, dataframe)

        nb_chunks = vector_store.add_chunks(
            document_id=document_id,
            filename=filename,
            file_type=file_type,
            chunks=chunk_texts,
            embeddings=embeddings,
            metadatas=chunk_metadatas,
        )
        sql_store.upsert_document(
            document_id=document_id,
            filename=filename,
            file_type=file_type,
            nb_chunks=nb_chunks,
            nb_records=nb_records,
            sql_table_name=sql_table_name,
            source_path=source_path,
        )
    except HTTPException:
        if existing_document is None:
            sql_store.drop_table_if_exists(sql_table_name)
            sql_store.delete_document(document_id)
            vector_store.delete_document(document_id)
            source_store.delete(source_path)
        raise
    except httpx.HTTPStatusError as exc:
        if existing_document is None:
            sql_store.drop_table_if_exists(sql_table_name)
            sql_store.delete_document(document_id)
            vector_store.delete_document(document_id)
            source_store.delete(source_path)
        if exc.response.status_code == 429:
            raise HTTPException(
                status_code=429,
                detail=(
                    "Limite de requêtes Vercel AI Gateway atteinte pour les embeddings. "
                    "Réessayez dans quelques minutes ou ajoutez des crédits sur votre compte Vercel."
                ),
            ) from exc
        raise HTTPException(status_code=502, detail=f"Ingestion failed: {exc}") from exc
    except Exception as exc:
        if existing_document is None:
            sql_store.drop_table_if_exists(sql_table_name)
            sql_store.delete_document(document_id)
            vector_store.delete_document(document_id)
            source_store.delete(source_path)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc

    duration_ms = int((time.perf_counter() - started_at) * 1000)
    return IngestionResult(
        document_id=document_id,
        filename=filename,
        file_type=file_type,
        nb_chunks=nb_chunks,
        nb_records=nb_records,
        duration_ms=duration_ms,
    )


def _extract_document(
    *,
    file_type: SupportedFileType,
    filename: str,
    content: bytes,
    ocr_dpi: int,
) -> tuple[ExtractedDocument, int, Any | None]:
    if file_type == "pdf":
        return extract_pdf_document(content, dpi=ocr_dpi), 0, None
    if file_type in {"png", "jpg", "jpeg", "webp"}:
        return extract_image_document(content, extension=f".{file_type}"), 0, None

    dataframe = load_csv(content) if file_type == "csv" else load_excel(content)
    extracted = ExtractedDocument(
        units=dataframe_to_text_rows(dataframe, filename),
        extraction_source="tabular",
        ocr_used=False,
    )
    return extracted, len(dataframe.index), dataframe


def _chunk_text_units(
    chunker: TextChunker,
    units: list[TextUnit],
    *,
    file_type: SupportedFileType,
) -> list[dict[str, object]]:
    chunk_payloads: list[dict[str, object]] = []
    document_kind = _document_kind(file_type)
    use_sections = document_kind != "table"

    for unit in units:
        for split_index, split_chunk in enumerate(
            chunker.split_unit(unit.text, use_sections=use_sections) or [],
            start=1,
        ):
            chunk_metadata: dict[str, str | int | bool] = {
                **unit.metadata,
                "chunk_split_index": split_index,
                "document_kind": document_kind,
            }
            if split_chunk.section_title:
                chunk_metadata["section_title"] = split_chunk.section_title
            chunk_payloads.append(
                {
                    "text": split_chunk.text,
                    "metadata": chunk_metadata,
                }
            )
    return chunk_payloads


def _document_kind(file_type: SupportedFileType) -> str:
    if file_type in {"csv", "xlsx", "xls"}:
        return "table"
    return "text"
