from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    vercel_ai_gateway_url: str = Field(
        default="https://ai-gateway.vercel.sh/v1",
        alias="VERCEL_AI_GATEWAY_URL",
    )
    vercel_ai_gateway_key: str = Field(
        default="",
        validation_alias=AliasChoices("VERCEL_AI_GATEWAY_KEY", "VERCEL_API_KEY_RAG_WORKSHOP"),
    )
    router_model: str = Field(default="google/gemini-3.1-flash-lite", alias="ROUTER_MODEL")
    answer_model: str = Field(default="openai/gpt-4o-mini", alias="ANSWER_MODEL")
    embedding_model: str = Field(default="alibaba/qwen3-embedding-4b", alias="EMBEDDING_MODEL")
    chroma_path: str = Field(default="./data/chroma_db", alias="CHROMA_PATH")
    sqlite_path: str = Field(default="./data/knowledge.db", alias="SQLITE_PATH")
    source_documents_path: str = Field(default="./data/source_documents", alias="SOURCE_DOCUMENTS_PATH")
    chunk_size: int = Field(default=500, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, alias="CHUNK_OVERLAP")
    max_upload_size_mb: int = Field(default=20, alias="MAX_UPLOAD_SIZE_MB")
    frontend_url: str = Field(default="http://localhost:3001", alias="FRONTEND_URL")
    ocr_dpi: int = Field(default=200, alias="OCR_DPI")
    vector_top_k: int = Field(default=20, alias="VECTOR_TOP_K")
    gateway_max_retries: int = Field(default=5, alias="GATEWAY_MAX_RETRIES")
    gateway_max_retry_delay_seconds: float = Field(
        default=60.0,
        alias="GATEWAY_MAX_RETRY_DELAY_SECONDS",
    )
    embedding_batch_size: int = Field(default=8, alias="EMBEDDING_BATCH_SIZE")
    embedding_batch_delay_seconds: float = Field(
        default=2.0,
        alias="EMBEDDING_BATCH_DELAY_SECONDS",
    )
    sql_preview_rows: int = 5

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parent.parent

    def resolve_path(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else (self.project_root / path).resolve()

    @property
    def chroma_dir(self) -> Path:
        return self.resolve_path(self.chroma_path)

    @property
    def sqlite_file(self) -> Path:
        return self.resolve_path(self.sqlite_path)

    @property
    def source_documents_dir(self) -> Path:
        return self.resolve_path(self.source_documents_path)

    @property
    def vector_collection_name(self) -> str:
        normalized = self.embedding_model.replace("/", "_").replace("-", "_").replace(".", "_")
        return f"knowledge_chunks_{normalized}"

    def ensure_directories(self) -> None:
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.sqlite_file.parent.mkdir(parents=True, exist_ok=True)
        self.source_documents_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
