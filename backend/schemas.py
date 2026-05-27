from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[ChatMessage] = Field(default_factory=list)


class DocumentOut(BaseModel):
    id: str
    filename: str
    type: str
    nb_chunks: int
    nb_records: int
    indexed_at: datetime
    can_reindex: bool = False


class KnowledgeStats(BaseModel):
    total_documents: int
    total_chunks: int
    total_records: int
    chroma_size_mb: float
    sqlite_size_mb: float


class KnowledgeOverview(BaseModel):
    documents: list[DocumentOut]
    stats: KnowledgeStats


class IngestResponse(BaseModel):
    document_id: str
    filename: str
    type: str
    nb_chunks: int
    nb_records: int
    duration_ms: int


class DeleteResponse(BaseModel):
    success: bool
    document_id: str


class PurgeResponse(BaseModel):
    success: bool
    deleted_documents: int


class ReindexResponse(BaseModel):
    document_id: str
    filename: str
    type: str
    nb_chunks: int
    nb_records: int
    duration_ms: int
