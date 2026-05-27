from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent.llm_client import VercelAIGatewayClient
from api.routes_chat import router as chat_router
from api.routes_ingest import router as ingest_router
from api.routes_knowledge import router as knowledge_router
from config import get_settings
from ingestion.embedder import GatewayEmbedder
from storage.source_store import SourceStore
from storage.sql_store import SQLStore
from storage.vector_store import VectorStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    gateway_client = VercelAIGatewayClient(
        base_url=settings.vercel_ai_gateway_url,
        api_key=settings.vercel_ai_gateway_key,
        max_retries=settings.gateway_max_retries,
        max_retry_delay_seconds=settings.gateway_max_retry_delay_seconds,
    )

    app.state.settings = settings
    app.state.sql_store = SQLStore(settings.sqlite_file)
    app.state.vector_store = VectorStore(settings.chroma_dir, settings.vector_collection_name)
    app.state.source_store = SourceStore(settings.source_documents_dir)
    app.state.embedder = GatewayEmbedder(
        gateway_client,
        settings.embedding_model,
        batch_size=settings.embedding_batch_size,
        batch_delay_seconds=settings.embedding_batch_delay_seconds,
    )
    app.state.gateway_client = gateway_client
    yield
    await gateway_client.close()


app = FastAPI(
    title="rag-workshop",
    description="Assistant IA RAG multi-source avec routage SQL / VECTOR.",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()
allowed_origins = list(
    dict.fromkeys([settings.frontend_url, "http://localhost:3000", "http://localhost:3001"])
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router, prefix="/api/ingest", tags=["ingest"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(knowledge_router, prefix="/api/knowledge", tags=["knowledge"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
