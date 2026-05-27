from __future__ import annotations

import uuid

from fastapi import APIRouter, File, Request, UploadFile, status

from ingestion.pipeline import ingest_document_bytes
from schemas import IngestResponse

router = APIRouter()


@router.post("/upload", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(request: Request, file: UploadFile = File(...)) -> IngestResponse:
    settings = request.app.state.settings
    sql_store = request.app.state.sql_store
    vector_store = request.app.state.vector_store
    embedder = request.app.state.embedder
    source_store = request.app.state.source_store
    content = await file.read()
    document_id = str(uuid.uuid4())
    result = await ingest_document_bytes(
        settings=settings,
        sql_store=sql_store,
        vector_store=vector_store,
        embedder=embedder,
        source_store=source_store,
        document_id=document_id,
        filename=file.filename or "",
        content=content,
    )
    return IngestResponse(
        document_id=result.document_id,
        filename=result.filename,
        type=result.file_type,
        nb_chunks=result.nb_chunks,
        nb_records=result.nb_records,
        duration_ms=result.duration_ms,
    )
