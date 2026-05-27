"""
Démo : visualiser la similarité sémantique entre phrases.
Lancer : python scripts/embed_demo.py
"""

from math import sqrt
import os

import httpx


API_KEY = os.getenv("VERCEL_AI_GATEWAY_KEY", "")
BASE_URL = os.getenv("VERCEL_AI_GATEWAY_URL", "https://ai-gateway.vercel.sh/v1")
MODEL = os.getenv("EMBEDDING_MODEL", "alibaba/qwen3-embedding-4b")

phrases = [
    "Les ventes ont augmenté en mars",
    "Le chiffre d'affaires de mars est en hausse",
    "La météo est nuageuse aujourd'hui",
]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    dot_product = sum(a * b for a, b in zip(left, right))
    left_norm = sqrt(sum(a * a for a in left))
    right_norm = sqrt(sum(b * b for b in right))
    return dot_product / (left_norm * right_norm)


if not API_KEY:
    raise RuntimeError("VERCEL_AI_GATEWAY_KEY must be set to run this demo.")

response = httpx.post(
    f"{BASE_URL}/embeddings",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    },
    json={
        "model": MODEL,
        "input": phrases,
    },
    timeout=60.0,
)
response.raise_for_status()
embeddings = [item["embedding"] for item in response.json()["data"]]

print("\n=== Similarité cosinus entre les phrases ===\n")
for i in range(len(phrases)):
    for j in range(i + 1, len(phrases)):
        sim = cosine_similarity(embeddings[i], embeddings[j])
        print(f"  [{i + 1}] vs [{j + 1}] : {sim:.3f}")
        print(f"        '{phrases[i][:50]}'")
        print(f"        '{phrases[j][:50]}'")
        print()
