"""Embeddings locaux (sentence-transformers) pour le notebook de présentation."""

from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer


DEFAULT_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


@lru_cache(maxsize=1)
def get_embedding_model(model_name: str = DEFAULT_MODEL_NAME) -> SentenceTransformer:
    return SentenceTransformer(model_name)


def embed_texts(texts: list[str], *, model_name: str = DEFAULT_MODEL_NAME) -> list[list[float]]:
    if not texts:
        return []
    model = get_embedding_model(model_name)
    vectors = model.encode(texts, convert_to_numpy=True, show_progress_bar=len(texts) > 16)
    return [vector.tolist() for vector in vectors]


def embed_query(query: str, *, model_name: str = DEFAULT_MODEL_NAME) -> list[float]:
    return embed_texts([query], model_name=model_name)[0]
