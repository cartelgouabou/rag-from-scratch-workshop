from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ingestion.pipeline import ingest_document_bytes
from schemas import DeleteResponse, DocumentOut, KnowledgeOverview, KnowledgeStats, PurgeResponse, ReindexResponse

router = APIRouter()


@router.get("/documents", response_model=KnowledgeOverview)
async def list_documents(request: Request) -> KnowledgeOverview:
    sql_store = request.app.state.sql_store
    vector_store = request.app.state.vector_store
    source_store = request.app.state.source_store

    active_chunk_counts = vector_store.get_document_chunk_counts()
    documents = [
        DocumentOut(
            **{
                **document,
                "nb_chunks": active_chunk_counts.get(document["id"], 0),
                "can_reindex": source_store.exists(document.get("source_path")),
            }
        )
        for document in sql_store.list_documents()
    ]
    sqlite_size = 0.0
    if sql_store.sqlite_file.exists():
        sqlite_size = round(sql_store.sqlite_file.stat().st_size / (1024 * 1024), 2)

    stats = KnowledgeStats(
        total_documents=len(documents),
        total_chunks=sum(document.nb_chunks for document in documents),
        total_records=sum(document.nb_records for document in documents),
        chroma_size_mb=vector_store.size_mb(),
        sqlite_size_mb=sqlite_size,
    )
    return KnowledgeOverview(documents=documents, stats=stats)


@router.get("/stats", response_model=KnowledgeStats)
async def get_stats(request: Request) -> KnowledgeStats:
    overview = await list_documents(request)
    return overview.stats


@router.delete("/purge", response_model=PurgeResponse)
async def purge_all(request: Request) -> PurgeResponse:
    sql_store = request.app.state.sql_store
    vector_store = request.app.state.vector_store
    source_store = request.app.state.source_store

    deleted_documents = len(sql_store.list_documents())
    sql_store.purge_all()
    vector_store.purge_all()
    source_store.purge_all()

    return PurgeResponse(success=True, deleted_documents=deleted_documents)


@router.delete("/documents/{document_id}", response_model=DeleteResponse)
async def delete_document(document_id: str, request: Request) -> DeleteResponse:
    sql_store = request.app.state.sql_store
    vector_store = request.app.state.vector_store
    source_store = request.app.state.source_store

    document = sql_store.delete_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    vector_store.delete_document(document_id)
    source_store.delete(document.get("source_path"))
    return DeleteResponse(success=True, document_id=document_id)


@router.post("/documents/{document_id}/reindex", response_model=ReindexResponse)
async def reindex_document(document_id: str, request: Request) -> ReindexResponse:
    settings = request.app.state.settings
    sql_store = request.app.state.sql_store
    vector_store = request.app.state.vector_store
    embedder = request.app.state.embedder
    source_store = request.app.state.source_store

    document = sql_store.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    source_path = document.get("source_path")
    if not isinstance(source_path, str) or not source_store.exists(source_path):
        raise HTTPException(
            status_code=409,
            detail="Le fichier source de ce document n'est plus disponible pour la reindexation.",
        )

    result = await ingest_document_bytes(
        settings=settings,
        sql_store=sql_store,
        vector_store=vector_store,
        embedder=embedder,
        source_store=source_store,
        document_id=document_id,
        filename=str(document["filename"]),
        content=source_store.read_bytes(source_path),
        existing_document=document,
    )
    return ReindexResponse(
        document_id=result.document_id,
        filename=result.filename,
        type=result.file_type,
        nb_chunks=result.nb_chunks,
        nb_records=result.nb_records,
        duration_ms=result.duration_ms,
    )
