from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import chromadb


def _sanitize_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
    sanitized: dict[str, str | int | float | bool] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, bool):
            sanitized[key] = value
        elif isinstance(value, int):
            sanitized[key] = int(value)
        elif isinstance(value, float):
            sanitized[key] = float(value)
        elif isinstance(value, str):
            sanitized[key] = value
        elif hasattr(value, "item"):
            item = value.item()
            if isinstance(item, bool):
                sanitized[key] = item
            elif isinstance(item, int):
                sanitized[key] = int(item)
            elif isinstance(item, float):
                sanitized[key] = float(item)
            else:
                sanitized[key] = str(item)
        else:
            sanitized[key] = str(value)
    return sanitized


class VectorStore:
    def __init__(self, chroma_dir: Path, collection_name: str = "knowledge_chunks") -> None:
        self.chroma_dir = chroma_dir
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=str(chroma_dir))
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_chunks(
        self,
        document_id: str,
        filename: str,
        file_type: str,
        chunks: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> int:
        if not chunks:
            return 0
        ids = [f"{document_id}:{index}" for index in range(len(chunks))]
        if metadatas is None:
            metadatas = [{} for _ in chunks]
        if len(metadatas) != len(chunks):
            raise ValueError("Each chunk must have a matching metadata entry.")

        collection_metadatas = [
            _sanitize_metadata(
                {
                    "document_id": document_id,
                    "filename": filename,
                    "type": file_type,
                    "chunk_index": index,
                    **metadata,
                }
            )
            for index, metadata in enumerate(metadatas)
        ]
        self.collection.add(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=collection_metadatas,
        )
        return len(chunks)

    def query(
        self,
        query_embedding: list[float],
        top_k: int,
        *,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        query_kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            query_kwargs["where"] = where
        if where_document:
            query_kwargs["where_document"] = where_document

        result = self.collection.query(**query_kwargs)
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        return [
            {
                "content": document,
                "metadata": metadata,
                "distance": distance,
            }
            for document, metadata, distance in zip(documents, metadatas, distances)
        ]

    def get_document_chunk_counts(self) -> dict[str, int]:
        result = self.collection.get(include=["metadatas"])
        counts: dict[str, int] = {}
        for metadata in result.get("metadatas", []):
            document_id = metadata.get("document_id")
            if not isinstance(document_id, str) or not document_id:
                continue
            counts[document_id] = counts.get(document_id, 0) + 1
        return counts

    def delete_document(self, document_id: str) -> None:
        self.collection.delete(where={"document_id": document_id})

    def purge_all(self) -> None:
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

    def close(self) -> None:
        """Release Chroma SQLite handles (required before deleting the index folder)."""
        self.client.close()

    def size_mb(self) -> float:
        total = sum(path.stat().st_size for path in self.chroma_dir.rglob("*") if path.is_file())
        return round(total / (1024 * 1024), 2)


def _close_existing_store(existing: Any) -> bool:
    """Close a store instance even if loaded from an older module version."""
    close_method = getattr(existing, "close", None)
    if callable(close_method):
        close_method()
        return True
    client = getattr(existing, "client", None)
    if client is not None and hasattr(client, "close"):
        client.close()
        return True
    return False


def _release_chroma_persist_path(target: Path) -> int:
    """Drop any in-process Chroma system still bound to this persist directory."""
    from chromadb.api.shared_system_client import SharedSystemClient

    path_id = str(target)
    released = 0
    while SharedSystemClient._identifier_to_refcount.get(path_id, 0) > 0:
        SharedSystemClient._release_system(path_id)
        released += 1
    return released


def reset_notebook_index(
    chroma_dir: Path,
    collection_name: str,
    existing: VectorStore | None = None,
) -> VectorStore:
    """Open a writable Chroma index for the presentation notebook.

    Closes any previous client on the same path before deleting files so
    Chroma's shared SQLite connection is released (avoids readonly DB errors).
    """
    target = Path(chroma_dir).resolve()
    if existing is not None:
        _close_existing_store(existing)
    _release_chroma_persist_path(target)
    if target.exists():
        shutil.rmtree(target)
    return VectorStore(target, collection_name)
