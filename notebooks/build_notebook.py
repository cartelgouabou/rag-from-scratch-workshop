"""Génère rag_atelier_presentation.ipynb (usage interne)."""

from __future__ import annotations

import json
from pathlib import Path


def md(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source}


def code(source: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "source": source, "outputs": []}


NOTEBOOK = Path(__file__).parent / "rag_atelier_presentation.ipynb"

cells = [
    md(
        """# Atelier RAG — présentation pas à pas

Ce notebook rejoue le pipeline **RAG sur un document PDF** de l'application **rag-from-scratch-workshop** :

1. Sélection et ingestion du PDF (extraction, chunking)
2. Embeddings et similarité cosinus
3. Indexation vectorielle (ChromaDB)
4. Retrieval (chunks les plus proches de la question)
5. Génération de réponse (sans RAG vs avec RAG)
6. Agent routeur (amélioration possible du pipeline)

> **Interactif** : déposez un **PDF** dans `data/samples/` avant d'exécuter les cellules."""
    ),
    md(
        """## Stack notebook vs backend

| Étape | Notebook (atelier) | Backend production |
|-------|-------------------|-------------------|
| Embeddings | `sentence-transformers` (local) | Vercel AI Gateway (`EMBEDDING_MODEL`) |
| Retrieval | Chroma L2, `VECTOR_TOP_K` | idem + rerank / diversification |
| Génération | Gateway — `WORKSHOP_ANSWER_MODEL` (Llama 3.2 ou Mistral 3B) | `ANSWER_MODEL` du `.env` |
| Routage | `heuristic_route` (démo §8) | LLM `ROUTER_MODEL` si clé Gateway |
| Vecteurs | Chroma `data/notebook_chroma/` | Chroma `data/chroma_db/` |

**Prérequis** : embeddings locaux sans clé API ; la **section 7** nécessite `VERCEL_AI_GATEWAY_KEY` et le choix du modèle atelier dans la cellule de code (voir ci-dessous)."""
    ),
    code(
        """import sys
from pathlib import Path

PROJECT_ROOT = Path.cwd().resolve()
if not (PROJECT_ROOT / "backend").exists():
    PROJECT_ROOT = PROJECT_ROOT.parent

BACKEND_DIR = PROJECT_ROOT / "backend"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
SAMPLES_DIR = PROJECT_ROOT / "data" / "samples"

for path in (BACKEND_DIR, NOTEBOOKS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import pandas as pd
from itables import show

print("Python:", sys.version.split()[0])
print("PROJECT_ROOT:", PROJECT_ROOT)
print("BACKEND_DIR:", BACKEND_DIR)
if sys.version_info < (3, 9):
    raise RuntimeError("Python 3.9+ requis pour ce notebook.")"""
    ),
    code(
        """from config import get_settings

settings = get_settings()
CHUNK_SIZE = settings.chunk_size
CHUNK_OVERLAP = settings.chunk_overlap
VECTOR_TOP_K = settings.vector_top_k
OCR_DPI = settings.ocr_dpi
EMBEDDING_MODEL_PROD = settings.embedding_model
ROUTER_MODEL_PROD = settings.router_model
ANSWER_MODEL_PROD = settings.answer_model

print("Paramètres clés (alignés sur config.py / .env):")
print(f"  CHUNK_SIZE={CHUNK_SIZE}, CHUNK_OVERLAP={CHUNK_OVERLAP}")
print(f"  VECTOR_TOP_K={VECTOR_TOP_K}, OCR_DPI={OCR_DPI}")
print(f"  Prod embeddings: {EMBEDDING_MODEL_PROD}")
print(f"  Prod routeur: {ROUTER_MODEL_PROD}")
print(f"  Prod réponse (.env): {ANSWER_MODEL_PROD}")
print("  Atelier génération: choisi en section 7 (WORKSHOP_ANSWER_MODEL_KEY)")"""
    ),
    md(
        """## 0 bis — Sélection du fichier PDF

**Consignes** : ce parcours suppose un **PDF** dans `data/samples/` (pas de branche SQL / CSV dans ce notebook).

- `DEMO_FILENAME = None` → utilise le **premier PDF** (ordre alphabétique) du dossier.
- `DEMO_FILENAME = "mon_fichier.pdf"` → utilise ce fichier précis.

Équivalent backend : upload depuis l'onglet *Knowledge* → [`ingest_document_bytes`](../backend/ingestion/pipeline.py)."""
    ),
    code(
        """from demo_paths import SAMPLES_DIR, list_pdf_candidates, load_demo_bytes

# None = premier PDF dans data/samples/ | sinon nom exact du fichier
DEMO_FILENAME = None  # ex: "Dossier_CIFRE_DermaScan_draft_v3.pdf"

demo_file, demo_bytes = load_demo_bytes(DEMO_FILENAME)

print(f"Dossier: {SAMPLES_DIR}")
print(f"PDF disponibles: {[p.filename for p in list_pdf_candidates()] or '(aucun)'}")
print(f"Fichier utilisé: {demo_file.filename}")
print(f"Type: {demo_file.file_type} | Branche: {demo_file.document_kind}")"""
    ),
    code(
        """DEMO_QUESTION = (
    "Quels sont les objectifs et les apports scientifiques du projet ?"
)

print("Question de démonstration:")
print(DEMO_QUESTION)"""
    ),
    md(
        """## 1 — Détection du type de fichier

**Rôle** : choisir le bon extracteur (PDF, image, CSV, Excel).

**Bibliothèque** : `pathlib` + mapping dans [`loader.py`](../backend/ingestion/loader.py) (`SUPPORTED_EXTENSIONS`).

**Backend** : identique — `detect_file_type(filename)`."""
    ),
    code(
        """from ingestion.loader import detect_file_type, SUPPORTED_EXTENSIONS

file_type = detect_file_type(demo_file.filename)
show(
    pd.DataFrame(
        [{"extension": ext, "type": typ} for ext, typ in sorted(SUPPORTED_EXTENSIONS.items())]
    )
)"""
    ),
    md(
        """## 2 — Extraction du texte

| Cas | Mécanisme | Bibliothèques |
|-----|-----------|---------------|
| PDF avec texte | Extraction native | `pdfplumber` |
| PDF scanné / image | OCR | `docTR` + `PyMuPDF` (fitz) |
| CSV / Excel | Lignes tabulaires | `pandas` |

**Backend** : [`_extract_document`](../backend/ingestion/pipeline.py) — même logique ci-dessous."""
    ),
    code(
        """from ingestion.loader import (
    extract_pdf_document,
    extract_image_document,
    load_csv,
    load_excel,
    dataframe_to_text_rows,
)
from ingestion.pipeline import _extract_document

extracted, nb_records, dataframe = _extract_document(
    file_type=file_type,
    filename=demo_file.filename,
    content=demo_bytes,
    ocr_dpi=OCR_DPI,
)

print(f"Source extraction: {extracted.extraction_source}")
print(f"OCR utilisé: {extracted.ocr_used}")
print(f"Nombre d'unités texte: {len(extracted.units)}")
print(f"Lignes tabulaires (si CSV/Excel): {nb_records}")

for index, unit in enumerate(extracted.units[:2], start=1):
    print(f"\\n--- Unité {index} (aperçu) ---")
    print(unit.text[:500])
    print("Métadonnées:", unit.metadata)"""
    ),
    md(
        """### 2b — OCR (optionnel, lent)

Si le PDF n'a pas de couche texte, le backend bascule sur DocTR. **Ne l'exécutez en live que si nécessaire** (modèle lourd, téléchargement)."""
    ),
    code(
        """# Décommentez pour forcer un test OCR sur une image/PDF scanné
# from ingestion.loader import extract_image_document
# ocr_doc = extract_image_document(demo_bytes, extension=Path(demo_file.filename).suffix)
# print(ocr_doc.extraction_source, len(ocr_doc.units))"""
    ),
    md(
        """## 3 — Chunking

**Rôle** : découper en morceaux indexables tout en gardant du contexte (sections Markdown, numérotation, titres en majuscules).

**Bibliothèque** : `langchain-text-splitters` (`RecursiveCharacterTextSplitter`) + heuristiques maison dans [`chunker.py`](../backend/ingestion/chunker.py).

**Backend** : [`_chunk_text_units`](../backend/ingestion/pipeline.py) — même appel."""
    ),
    code(
        """from ingestion.chunker import TextChunker
from ingestion.pipeline import _chunk_text_units

chunker = TextChunker(CHUNK_SIZE, CHUNK_OVERLAP)
chunk_payloads = _chunk_text_units(chunker, extracted.units, file_type=file_type)

chunks_df = pd.DataFrame(
    [
        {
            "index": i,
            "chars": len(p["text"]),
            "section_title": (p["metadata"] or {}).get("section_title"),
            "preview": p["text"][:200].replace("\\n", " "),
        }
        for i, p in enumerate(chunk_payloads, start=1)
    ]
)
print(f"Nombre de chunks: {len(chunk_payloads)}")
show(chunks_df)"""
    ),
    md(
        """## 4 — Embeddings et similarité cosinus

**Rôle** : représenter le sens des textes par des vecteurs numériques.

| | Notebook | Backend |
|---|----------|---------|
| Modèle | `paraphrase-multilingual-MiniLM-L12-v2` | Gateway + `qwen3-embedding-4b` (config) |
| Coût | Local, gratuit | Quota / crédits Vercel |

La **similarité cosinus** mesure l'angle entre deux vecteurs (1 = très proche, 0 = orthogonal).

Les exemples ci-dessous utilisent trois phrases liées à l'activité de dépistage dermatologique (et une phrase hors sujet pour le contraste)."""
    ),
    md(
        """### Comment un texte devient un vecteur

Chaque phrase est transformée en un **vecteur dense** (liste de nombres) par le modèle local `sentence-transformers` :

1. **Tokenisation** — la phrase est découpée en sous-mots (tokens).
2. **Encodeur Transformer** — chaque token reçoit une représentation numérique (`paraphrase-multilingual-MiniLM-L12-v2`, typiquement **384 dimensions**).
3. **Pooling** — moyenne des vecteurs de tokens → **un seul vecteur par phrase**.
4. **Utilisation** — ces vecteurs servent à comparer le sens des textes (recherche sémantique, RAG).

*Backend production* : même logique conceptuelle, mais les vecteurs sont produits via **Vercel AI Gateway** (`EMBEDDING_MODEL` dans `.env`)."""
    ),
    code(
        """from local_embedder import DEFAULT_MODEL_NAME, embed_texts

phrases = [
    "Les centres réalisent un dépistage des cancers de la peau par examen clinique, cartographie corporelle et dermoscopie.",
    "L'outil d'intelligence artificielle classe les lésions cutanées à partir d'images dermoscopiques du corpus clinique.",
    "Le chiffre d'affaires trimestriel a augmenté grâce à la hausse des ventes en mars.",
]
phrase_ids = ["P1", "P2", "P3"]

phrase_vectors = embed_texts(phrases)
print(f"Modèle : {DEFAULT_MODEL_NAME}")

vectors_df = pd.DataFrame(
    [
        {
            "id": phrase_ids[i],
            "phrase": phrases[i],
            "dimensions": len(phrase_vectors[i]),
            "apercu_vecteur": [round(x, 4) for x in phrase_vectors[i][:8]],
        }
        for i in range(len(phrases))
    ]
)
show(vectors_df)"""
    ),
    md(
        """### Similarité cosinus

Deux vecteurs $A$ et $B$ de dimension $d$ :

$$
\\text{sim}_{\\cos}(A, B) = \\frac{A \\cdot B}{\\|A\\| \\, \\|B\\|} = \\frac{\\sum_{k=1}^{d} A_k \\, B_k}{\\sqrt{\\sum_{k=1}^{d} A_k^2} \\, \\sqrt{\\sum_{k=1}^{d} B_k^2}}
$$

- **Proche de 1** : directions similaires → sens proches dans l'espace sémantique.
- **Proche de 0** : peu liés.

On s'attend à ce que **P1 ↔ P2** (dépistage / IA dermatologique) aient un score plus élevé que **P1 ↔ P3** et **P2 ↔ P3** (phrase hors domaine)."""
    ),
    code(
        """from math import sqrt

import matplotlib.pyplot as plt
import numpy as np


def cosine_similarity(left, right):
    dot = sum(a * b for a, b in zip(left, right))
    return dot / (sqrt(sum(a * a for a in left)) * sqrt(sum(b * b for b in right)))


matrix = np.zeros((len(phrases), len(phrases)))
for i in range(len(phrases)):
    for j in range(len(phrases)):
        matrix[i, j] = cosine_similarity(phrase_vectors[i], phrase_vectors[j])

fig, ax = plt.subplots(figsize=(5, 4))
im = ax.imshow(matrix, vmin=0, vmax=1, cmap="Blues")
ax.set_xticks(range(len(phrases)), labels=phrase_ids)
ax.set_yticks(range(len(phrases)), labels=phrase_ids)
plt.colorbar(im, ax=ax, label="cosinus")
ax.set_title("Similarité cosinus — exemples métier")
plt.show()

for i in range(len(phrases)):
    for j in range(i + 1, len(phrases)):
        print(f"{phrase_ids[i]} vs {phrase_ids[j]}: {matrix[i, j]:.3f}")
        print(f"  {phrases[i][:60]}{'…' if len(phrases[i]) > 60 else ''}")
        print(f"  {phrases[j][:60]}{'…' if len(phrases[j]) > 60 else ''}")"""
    ),
    md(
        """**Note** : Chroma renvoie une *distance* (souvent L2), pas directement le cosinus. Le rerank backend utilise `similarity = 1 / (1 + distance)` dans [`_rerank_candidates`](../backend/api/routes_chat.py)."""
    ),
    md(
        """## 5 — Indexation vectorielle (ChromaDB)

### Qu'est-ce que l'indexation ?

L'**indexation** consiste à enregistrer chaque **chunk** de texte avec son **embedding** (vecteur numérique) dans une **base vectorielle**, afin de pouvoir les retrouver plus tard par **similarité sémantique** avec une question.

Ce n'est pas le simple stockage du PDF sur disque : on construit un index consultable, comme une bibliothèque où chaque fiche (chunk) a une « coordonnée de sens » (typiquement **384 dimensions** avec le modèle du notebook).

### Ce qui est stocké dans Chroma (par entrée)

| Élément | Description |
|---------|-------------|
| `id` | Identifiant unique, ex. `{document_id}:0` |
| `document` | Texte du chunk |
| `embedding` | Vecteur produit par `embed_texts` |
| `metadata` | `filename`, `chunk_index`, `section_title`, `page_number`, etc. |

Implémentation : [`VectorStore.add_chunks`](../backend/storage/vector_store.py) — même classe que l'application.

### Dossiers et reproductibilité

- **Notebook** : `data/notebook_chroma/` (index de démo, séparé de la prod).
- **Production** : `data/chroma_db/` (index persistant de l'app).

**Ré-exécuter la cellule d'indexation** : le notebook ferme d'abord le client Chroma (`client.close()`) puis recrée le dossier (évite l'erreur SQLite *readonly database*).

On réutilise ici `chunk_payloads` (section 3) et le même modèle d'embedding que la section 4."""
    ),
    code(
        """import importlib
import uuid

import storage.vector_store as _vector_store_module
importlib.reload(_vector_store_module)

from local_embedder import embed_texts
from storage.vector_store import reset_notebook_index

# --- Étape 1 : préparer l'index notebook (ré-exécutable dans le même kernel) ---
NOTEBOOK_CHROMA = PROJECT_ROOT / "data" / "notebook_chroma"
collection_name = "notebook_presentation_chunks"

try:
    _previous_store = vector_store
    if not callable(getattr(_previous_store, "close", None)):
        _previous_store = None  # instance créée avant reload du module
except NameError:
    _previous_store = None

vector_store = reset_notebook_index(
    NOTEBOOK_CHROMA,
    collection_name,
    existing=_previous_store,
)
print("Index Chroma (notebook):", NOTEBOOK_CHROMA)
print("Client Chroma prêt (ancien client fermé avant recréation du dossier).")

# --- Étape 2 : identifiant document pour cette passe d'indexation ---
document_id = str(uuid.uuid4())
print("document_id:", document_id)

# --- Étape 3 : préparer textes et métadonnées depuis chunk_payloads ---
chunk_texts = [p["text"] for p in chunk_payloads]
chunk_metadatas = [p["metadata"] for p in chunk_payloads]
print(f"Chunks à indexer: {len(chunk_texts)}")

# --- Étape 4 : encoder tous les chunks en vecteurs (même modèle que section 4) ---
embeddings = embed_texts(chunk_texts)
print(f"Embeddings générés: {len(embeddings)} x {len(embeddings[0])} dimensions")

# --- Étape 5 : indexer dans Chroma (ids = document_id:chunk_index) ---
nb_indexed = vector_store.add_chunks(
    document_id=document_id,
    filename=demo_file.filename,
    file_type=file_type,
    chunks=chunk_texts,
    embeddings=embeddings,
    metadatas=chunk_metadatas,
)

# --- Étape 6 : contrôle — nombre indexé + aperçu des métadonnées ---
print(f"Chunks indexés dans Chroma: {nb_indexed}")
if chunk_metadatas:
    print("Exemple métadonnées (1er chunk):", chunk_metadatas[0])

indexed_preview_df = pd.DataFrame(
    [
        {
            "chunk_index": i,
            "filename": demo_file.filename,
            "section_title": (p["metadata"] or {}).get("section_title"),
            "page_number": (p["metadata"] or {}).get("page_number"),
            "chars": len(p["text"]),
            "dimensions": len(embeddings[i]),
            "apercu_vecteur": [round(x, 4) for x in embeddings[i][:8]],
        }
        for i, p in enumerate(chunk_payloads[:3], start=0)
    ]
)
print("Aperçu des 3 premiers chunks indexés:")
show(indexed_preview_df)"""
    ),
    md(
        """## 6 — Retrieval (recherche vectorielle)

### Qu'est-ce que le retrieval ?

Le **retrieval** (récupération) répond à la question : *« Quels passages de mon PDF sont les plus proches de la question de l'utilisateur ? »*

On transforme la question en vecteur, on interroge Chroma, puis on obtient une liste de **candidats** (chunks) classés par **distance** (plus la distance est faible, plus le chunk est jugé proche).

Le schéma ci-dessous est généré par la cellule suivante.

### Métriques de proximité

En recherche vectorielle, on compare la question $q$ et un chunk $c$ dans le **même espace d'embeddings**. Plusieurs métriques sont possibles :

- **Distance euclidienne (L2)** — distance géométrique entre les deux points
- **Similarité cosinus** — angle entre les vecteurs (direction)
- **Produit scalaire** (inner product) : $q \\cdot c = \\sum_{k=1}^{d} q_k \\, c_k$

### Distance utilisée dans cette démo : L2

Pour illustrer le retrieval, nous utilisons la **distance euclidienne** renvoyée par Chroma (métrique par défaut de l'index) :

$$
d_{\\text{L2}}(q, c) = \\| q - c \\| = \\sqrt{\\sum_{k=1}^{d} (q_k - c_k)^2}
$$

**Plus la distance est faible**, plus le chunk est proche de la question.

### Paramètres importants

- **`VECTOR_TOP_K`** (dans `.env`) : nombre de chunks renvoyés par Chroma, classés par distance L2 croissante.

Même logique de requête que [`vector_store.query`](../backend/storage/vector_store.py) ; le backend ajoute ensuite rerank et diversification (voir section 9 — pistes d'amélioration)."""
    ),
    code(
        """import matplotlib.pyplot as plt

steps = [
    "Question\\nutilisateur",
    "Embedding\\nquestion",
    "Requête Chroma\\n(top_k)",
    "Chunks\\ncandidats",
]
fig, ax = plt.subplots(figsize=(11, 2.2))
ax.set_xlim(0, len(steps))
ax.set_ylim(0, 1)
ax.axis("off")
for i, label in enumerate(steps):
    x = i + 0.5
    ax.text(
        x,
        0.55,
        label,
        ha="center",
        va="center",
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#e8f4fc", edgecolor="#2b6cb0"),
    )
    if i < len(steps) - 1:
        ax.annotate(
            "",
            xy=(i + 1.05, 0.55),
            xytext=(i + 0.95, 0.55),
            arrowprops=dict(arrowstyle="->", color="#2b6cb0", lw=1.5),
        )
ax.set_title("Pipeline retrieval (aperçu)", fontsize=12, pad=12)
plt.tight_layout()
plt.show()"""
    ),
    code(
        """from local_embedder import embed_query

# --- Étape 1 : rappel de la question ---
print("Question:", DEMO_QUESTION)

# --- Étape 2 : vecteur de la question (même espace que les chunks) ---
query_embedding = embed_query(DEMO_QUESTION)
print(f"Vecteur question: {len(query_embedding)} dimensions")

# --- Étape 3 : requête Chroma (top_k chunks) ---
print(f"Nombre de chunks demandés: {VECTOR_TOP_K}")
retrieved_chunks = vector_store.query(query_embedding, VECTOR_TOP_K)
print(f"Chunks récupérés: {len(retrieved_chunks)}")

# --- Étape 4 : tableau des candidats (distance L2, section, aperçu) ---
retrieval_df = pd.DataFrame(
    [
        {
            "rang": i,
            "distance": round(float(c.get("distance", 0)), 4),
            "filename": (c.get("metadata") or {}).get("filename"),
            "section": (c.get("metadata") or {}).get("section_title"),
            "preview": str(c.get("content", ""))[:120],
        }
        for i, c in enumerate(retrieved_chunks, start=1)
    ]
)
show(retrieval_df)"""
    ),
    md(
        """## 7 — Génération finale (Vercel AI Gateway)

**Rôle** : produire une réponse en langage naturel et **comparer l'effet du contexte documentaire**.

### Choix du modèle (atelier)

Dans la **cellule de code ci-dessous**, modifiez `WORKSHOP_ANSWER_MODEL_KEY` :

| Clé | Identifiant Gateway |
|-----|---------------------|
| `llama-3.2` | `meta/llama-3.2-3b` (ID Gateway, sans suffixe `-instruct`) |
| `mistral-3b` | `mistral/ministral-3b` |

Ce choix est **indépendant** de `ANSWER_MODEL` en production (`ANSWER_MODEL_PROD` affiché en intro).

### Comparaison sans RAG / avec RAG

1. **Sans RAG** — le modèle répond à partir de ses connaissances générales (risque d'hallucination ou d'imprécision).
2. **Avec RAG** — même question + les chunks `retrieved_chunks` injectés dans le prompt (`VECTOR_PROMPT` du backend).

| | Détail |
|---|--------|
| Client | [`VercelAIGatewayClient`](../backend/agent/llm_client.py) |
| Prérequis | `VERCEL_AI_GATEWAY_KEY` renseignée à la racine du projet |

> **Limite free tier** : deux appels rapprochés sur Llama/Mistral peuvent renvoyer **429**. Le notebook utilise **deux cellules** et une pause configurable entre les appels."""
    ),
    code(
        """import asyncio

import httpx
import nest_asyncio
from agent.llm_client import VercelAIGatewayClient
from api.routes_chat import VECTOR_PROMPT

# --- Choix du modèle atelier (modifier ici) ---
WORKSHOP_ANSWER_MODELS = {
    "llama-3.2": "meta/llama-3.2-3b",
    "mistral-3b": "mistral/ministral-3b",
}
WORKSHOP_ANSWER_MODEL_KEY = "llama-3.2"  # "llama-3.2" | "mistral-3b"
WORKSHOP_GATEWAY_PAUSE_SECONDS = 25  # pause avant l'appel « avec RAG » (free tier Gateway)

if WORKSHOP_ANSWER_MODEL_KEY not in WORKSHOP_ANSWER_MODELS:
    raise ValueError(
        f"WORKSHOP_ANSWER_MODEL_KEY invalide: {WORKSHOP_ANSWER_MODEL_KEY!r}. "
        f"Choix: {list(WORKSHOP_ANSWER_MODELS)}"
    )
WORKSHOP_ANSWER_MODEL = WORKSHOP_ANSWER_MODELS[WORKSHOP_ANSWER_MODEL_KEY]

nest_asyncio.apply()

gateway = VercelAIGatewayClient(
    settings.vercel_ai_gateway_url,
    settings.vercel_ai_gateway_key,
    max_retries=settings.gateway_max_retries,
    max_retry_delay_seconds=settings.gateway_max_retry_delay_seconds,
)

if not gateway.is_configured:
    raise RuntimeError(
        "VERCEL_AI_GATEWAY_KEY manquante. Copiez .env.example vers .env et renseignez la clé."
    )


async def workshop_gateway_complete(*, system: str, user: str, max_tokens: int) -> str:
    try:
        return await gateway.complete(
            model=WORKSHOP_ANSWER_MODEL,
            system=system,
            user=user,
            max_tokens=max_tokens,
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            raise RuntimeError(
                "Limite Vercel AI Gateway (429) — free tier sur ce modèle. "
                f"Attendez {WORKSHOP_GATEWAY_PAUSE_SECONDS}s puis réexécutez la cellule « Avec RAG », "
                "ou augmentez WORKSHOP_GATEWAY_PAUSE_SECONDS / passez à des crédits payants."
            ) from None
        raise


print(f"Modèle atelier: {WORKSHOP_ANSWER_MODEL} ({WORKSHOP_ANSWER_MODEL_KEY})")
print(f"Modèle prod (.env, info): {ANSWER_MODEL_PROD}\\n")

print("=== Sans RAG (question seule) ===\\n")
answer_sans_rag = asyncio.run(
    workshop_gateway_complete(
        system="Tu réponds en français de façon concise.",
        user=DEMO_QUESTION,
        max_tokens=400,
    )
)
print(answer_sans_rag)"""
    ),
    code(
        """# --- Contexte RAG depuis les chunks retrieval (section 6) ---
context_blocks = []
for index, item in enumerate(retrieved_chunks, start=1):
    meta = item.get("metadata") or {}
    heading = meta.get("filename", "unknown")
    section = meta.get("section_title")
    if isinstance(section, str) and section:
        heading = f"{heading} [{section}]"
    context_blocks.append(f"Source {index}: {heading}\\n{item.get('content', '')}")

combined_context = "\\n\\n".join(context_blocks)
user_prompt_rag = (
    f"Question: {DEMO_QUESTION}\\n\\n"
    f"Contexte:\\n{combined_context}"
)

print("--- Contexte injecté (aperçu) ---\\n")
print(user_prompt_rag[:1500], ("..." if len(user_prompt_rag) > 1500 else ""), "\\n")

print(
    f"Pause {WORKSHOP_GATEWAY_PAUSE_SECONDS}s avant l'appel Gateway (évite 429 free tier)..."
)
asyncio.run(asyncio.sleep(WORKSHOP_GATEWAY_PAUSE_SECONDS))

print("=== Avec RAG (question + contexte documentaire) ===\\n")
answer_avec_rag = asyncio.run(
    workshop_gateway_complete(
        system=VECTOR_PROMPT,
        user=user_prompt_rag,
        max_tokens=500,
    )
)
print(answer_avec_rag)"""
    ),
    md(
        """## 8 — Agent routeur (améliorer le RAG)

Les sections 1 à 7 montrent un pipeline **PDF → retrieval → génération**. En production, on peut **améliorer** ce RAG avec un **agent routeur** qui choisit l'outil avant d'interroger les données :

| Route | Outil |
|-------|--------|
| `VECTOR` | Base vectorielle (PDF, images OCR) |
| `SQL` | Tables CSV / Excel indexées |
| `BOTH` | Les deux sources combinées |

**Notebook** : démo avec l'heuristique [`heuristic_route`](../backend/agent/router.py) (sans appel LLM).

**Backend** : si la clé Gateway est configurée, le routeur LLM (`ROUTER_MODEL`) remplace l'heuristique ([`route_question`](../backend/agent/router.py))."""
    ),
    code(
        """from agent.router import ROUTER_PROMPT, heuristic_route

print("ROUTER_PROMPT (extrait backend):\\n")
print(ROUTER_PROMPT[:600], "...\\n")

questions = [
    ("PDF — question démo", DEMO_QUESTION),
    (
        "PDF — reformulation",
        "Quelles informations sur la dermoscopie figurent dans le document ?",
    ),
    (
        "SQL — KPI centres (exemple)",
        "Combien de patients au centre bastille dans example.csv ?",
    ),
]

for label, question in questions:
    decision = heuristic_route(question)
    print(f"\\n[{label}] {question}")
    print(f"  → route={decision.route} | confidence={decision.confidence:.2f}")
    print(f"  → reason={decision.reason}")"""
    ),
    md(
        """## 9 — Synthèse

| Étape | Fichier backend | Ce que vous venez de voir |
|-------|-----------------|---------------------------|
| Upload PDF | `routes_ingest.py` / `pipeline.py` | PDF depuis `data/samples/` |
| Extraction | `loader.py` | `extracted.units` |
| Chunking | `chunker.py` | `chunk_payloads` |
| Embeddings | `embedder.py` (Gateway) | `local_embedder.py` |
| Index | `vector_store.py` | Chroma `notebook_chroma/` |
| Retrieval | `vector_store.py` | `query` avec `VECTOR_TOP_K` |
| Génération | `routes_chat.py` + Gateway | sans RAG vs avec RAG (`WORKSHOP_ANSWER_MODEL`) |
| Routeur | `router.py` | `heuristic_route` (§8) |

*Notebook* : retrieval direct (distance L2). *Production* : sur-rappel, rerank, diversification, Gateway (voir cellules suivantes)."""
    ),
    md(
        """### Pistes d'amélioration : techniques, méthodes et outils

Bonnes pratiques pour améliorer un RAG en production. L'optimisation se joue à **chaque étape** du pipeline — le découpage naïf ou la seule recherche vectorielle sont des pièges fréquents.

#### Grandes leviers d'optimisation (état de l'art)

- **Chunking sémantique / structurel** — Ne pas couper « à la va-vite » par taille fixe : préserver titres, paragraphes et enchaînements logiques ; pour documents non structurés, faire superviser le découpage par l'IA (segments cohérents).
- **Recherche hybride + métadonnées** — Vecteurs seuls insuffisent souvent : combiner **BM25** (mots-clés exacts) et filtres **metadata** (date, auteur, géographie, type de doc).
- **GraphRAG** — Graphe de connaissances pour relier entités (personnes, lieux, concepts) **entre documents** ; navigation relationnelle que les embeddings plats ne capturent pas.
- **Reranking** — Souvent le **plus gros gain qualité** après un premier retrieval : modèle dédié (ex. Cohere Rerank) pour ne garder que les passages vraiment utiles avant le LLM.
- **Prompt structuré (XML)** — Balises `<instruction>`, `<context>`, `<question>` pour séparer clairement consignes, sources et requête utilisateur.
- **Scratchpad (brouillon)** — Sur contextes longs : forcer une étape intermédiaire (extraire faits / variables pertinentes, raisonnement CoT) **avant** la réponse finale → meilleure fiabilité.

Détail par phase ci-dessous (techniques | idée | outils).

#### Ingestion et préparation des documents

| Technique | Idée | Outils / écosystème |
|-----------|------|---------------------|
| PDF natif vs OCR | Texte extractible d'abord ; OCR si scan (DPI, contraste) | pdfplumber, PyMuPDF, DocTR, Tesseract |
| Nettoyage | Supprimer en-têtes/pieds de page, doublons, artefacts | règles métier, Unstructured |
| Métadonnées riches | page, section, type, date → filtres et citations | stockage Chroma / SQL, pipeline d'ingestion |

#### Chunking et indexation

| Technique | Idée | Outils / écosystème |
|-----------|------|---------------------|
| Taille / overlap | `CHUNK_SIZE`, `CHUNK_OVERLAP` selon densité du document | LangChain splitters, LlamaIndex |
| Découpe par structure | Respecter titres, paragraphes, tableaux | chunker par sections (comme `chunker.py`) |
| Chunking sémantique / IA | Segments logiques ; IA pour docs non structurés | LlamaIndex semantic splitter, Unstructured |
| Parent–child / small-to-big | Petits chunks pour la recherche ; passage élargi pour le LLM | LlamaIndex, archi « parent document » |
| Choix d'embedding | Modèle multilingue, domaine proche, même modèle index + requête | sentence-transformers, OpenAI, Voyage, Gateway |
| Réindexation | Obligatoire si changement de modèle ou de chunking | job batch, onglet Knowledge |

#### Retrieval

| Technique | Idée | Outils / écosystème |
|-----------|------|---------------------|
| Sur-rappel | Récupérer `top_k × N` candidats avant sélection finale | paramètre `candidate_count` |
| Reranking lexical | Overlap mots, BM25 en complément du vecteur | BM25, Elasticsearch |
| Reranking cross-encoder | **Gain qualité souvent maximal** — score (question, passage) | bge-reranker, **Cohere Rerank**, Jina |
| Diversification | Éviter 10 chunks du même PDF ; MMR ou quota par document | `_diversify_results` en prod |
| Recherche hybride | Dense + sparse (mots exacts, acronymes, noms propres) | Chroma hybrid, LanceDB, Vespa |
| GraphRAG | Relations entités cross-documents (graphe + vecteurs) | Microsoft GraphRAG, Neo4j, LlamaIndex Property Graph |
| Filtres metadata | Restreindre par `filename`, date, auteur, géo | `where` Chroma |
| Multi-query / HyDE | Plusieurs reformulations ou document hypothétique puis embedding | LangChain, LlamaIndex |

#### Requête et orchestration

| Technique | Idée | Outils / écosystème |
|-----------|------|---------------------|
| Reformulation | Clarifier la question avant embedding | LLM léger |
| Décomposition | Sous-questions puis fusion des contextes | agents, LangGraph |
| Routage multi-sources | SQL vs vecteur vs les deux | `router.py`, `ROUTER_MODEL` |
| Cache | Embeddings de questions fréquentes | Redis, cache applicatif |

#### Génération

| Technique | Idée | Outils / écosystème |
|-----------|------|---------------------|
| Prompt grounded | « Réponds uniquement avec le contexte » ; refus si insuffisant | `VECTOR_PROMPT` |
| Prompt XML structuré | Balises pour séparer instruction / contexte / question | templates XML dans le system prompt |
| Scratchpad / CoT | Extraire d'abord les faits utiles, puis répondre | prompting multi-étapes, agents |
| Citations | Lier chaque affirmation à une source | prompting + post-traitement |
| Compression de contexte | Réduire les tokens avant le LLM | LLMLingua, extraction de phrases |
| Réglages LLM | Température basse, `max_tokens`, modèle coût/qualité | Gateway, OpenAI, etc. |

#### Observabilité et ops

| Technique | Idée | Outils / écosystème |
|-----------|------|---------------------|
| Traçabilité | Logs des chunks, scores, latences | Langfuse, LangSmith, Arize Phoenix |
| Coût et SLO | Tokens, p95 latence, taux d'erreur | dashboards, alertes |

**Déjà dans ce dépôt (production)** — voir [`routes_chat.py`](../backend/api/routes_chat.py) et [`router.py`](../backend/agent/router.py) :

- Sur-rappel + rerank lexical (overlap + distance L2) + diversification par document.
- Filtre automatique sur le nom de fichier dans la question.
- Routeur SQL / vecteur / both avec `ROUTER_MODEL` si clé Gateway."""
    ),
    md(
        """### Perspectives : vigilance et architecture

Points de vigilance pour un RAG **en production**, au-delà de la démo notebook.

#### RAG vs fine-tuning

- **RAG** : données **dynamiques**, **privées** ou confidentielles (dossiers médicaux, relevés bancaires, PDF métier) — le modèle lit le corpus à la volée sans l'embarquer dans ses poids.
- **Fine-tuning** sur ces corpus : risque de **fuite** d'information, coût de réentraînement, **obsolescence** dès que les documents changent.

#### Passage à l'échelle

- Beaucoup de systèmes « fonctionnent » sur un **petit** jeu en mémoire ; à **millions de documents**, la pertinence et les **I/O disque** deviennent critiques.
- Anticiper : dimensionnement de l'index, sharding, cache, benchmarks sur volume réaliste (pas seulement le PDF atelier).

#### Sécurité

- Le contexte injecté peut placer le LLM dans une situation **hors distribution** : document apparemment anodin + requête malveillante → le modèle peut **affaiblir** ses garde-fous habituels.
- Mitigations : contrôle des sources indexées, politiques d'upload, **red teaming**, filtrage en amont.

#### Coût et infrastructure

- À grande échelle, l'architecture **serverless** ou le **découplage stockage / calcul** aide à maîtriser les coûts (vs serveurs toujours actifs) — souvent un facteur 10× à 100× sur le coût unitaire selon la charge."""
    ),
    md(
        """### Évaluer un RAG : méthodes et métriques

Ne pas se fier uniquement à la **similarité cosinus** en démo : mesurer retrieval et fidélité sur un **jeu de référence** (20–50 questions représentatives de vos PDF métier).

#### Sortir du « vibe check »

En revue technique, **bannir les adjectifs** (« mieux », « moins bien », « pas mal ») au profit de **mesures binaires ou chiffrées** : Recall@k, faithfulness, taux d'échec, latence p95.

#### Évaluations simples et peu coûteuses

Avant un **LLM-as-a-judge** systématique (coûteux, lent, biaisé), privilégier des signaux **rapides** :

| Signal | Exemple |
|--------|---------|
| RegEx / règles | Format de réponse, champs obligatoires présents |
| Longueur / compression | Ratio taille réponse vs contexte injecté |
| Entités nommées (NER) | La réponse cite-t-elle les entités attendues du chunk ? |
| Hit binaire | Chunk gold présent oui/non dans le top-k |

#### Segmenter l'espace des requêtes

Analyser les **types de questions** utilisateurs pour diagnostiquer les échecs :

- **Manque de capacité** — il manque une brique (métadonnée, colonne SQL, rerank, filtre) : améliorer le pipeline.
- **Manque d'inventaire** — le document ou la ligne n'existe pas dans le corpus : enrichir les sources, pas le modèle.

#### Gouvernance et red teaming

Dans les secteurs régulés : impliquer des **experts métier** (juristes, journalistes) ; taxonomies de risques ; tests **fraude**, **désinformation**, **injection** via documents indexés.

#### Méthodes d'évaluation

| Méthode | Description | Quand l'utiliser |
|---------|-------------|------------------|
| **Golden set** | Questions + réponses ou passages de référence + documents de test | Régression à chaque changement (chunking, embedding, rerank) |
| **Évaluation humaine** | Annotateurs notent pertinence et fidélité | Validation métier avant mise en prod |
| **LLM-as-a-judge** | Un LLM note la réponse par rapport au contexte | Automatisation à grande échelle (biais possibles) |
| **A/B en production** | Deux configurations, métriques qualité + business | Après une baseline offline |

**Frameworks** (implémentent souvent plusieurs métriques) : **RAGAS**, **DeepEval**, **TruLens**, **LangSmith**.

#### Métriques retrieval (qualité de la recherche)

*Prérequis* : savoir quels chunks sont **pertinents** pour chaque question (annotation humaine ou référence).

| Métrique | Définition | Calcul |
|----------|------------|--------|
| **Recall@k** | Fraction des chunks pertinents retrouvés dans le top-k | (nb pertinents dans top-k) / (nb pertinents totaux), moyenne sur les questions |
| **Hit Rate@k** (Success@k) | La recherche a-t-elle trouvé au moins un bon chunk ? | Pour chaque question : 1 si ≥1 pertinent dans top-k, sinon 0 ; puis **moyenne** |
| **MRR** | Pénalise les bons résultats trop bas dans la liste | Pour chaque question : `1 / rang_du_premier_pertinent` (0 si aucun) ; puis **moyenne** (Mean Reciprocal Rank) |
| **NDCG@k** | Prend en compte l'**ordre** et des niveaux de pertinence (0, 1, 2…) | **DCG@k** = Σ (2^rel_i − 1) / log₂(i+1) sur les rangs i≤k ; **NDCG** = DCG / IDCG (IDCG = DCG si ordre parfait) |

#### Métriques génération et contexte (qualité de la réponse)

| Métrique | Définition | Calcul (typique) |
|----------|------------|------------------|
| **Faithfulness** (groundedness) | La réponse est-elle **supportée** par le contexte (pas d'hallucination) ? | LLM-judge ou NLI : score 0–1 « la réponse découle des passages » ; **moyenne** sur le jeu |
| **Answer relevancy** | La réponse **répond-elle** à la question ? | Similarité embedding(question, réponse) ou score LLM-judge ; **moyenne** |
| **Context precision** | Les chunks envoyés au LLM sont-ils **utiles** (peu de bruit) ? | (chunks pertinents dans top-k) / k ; **moyenne** par question |
| **Context recall** | Le contexte **couvre-t-il** l'information nécessaire ? | Part des faits de la référence présents dans l'union des chunks (souvent jugé par LLM) |

#### Métriques ops (complément)

| Métrique | Définition | Calcul |
|----------|------------|--------|
| **Latence** | Temps retrieval + génération | p50 / p95 en secondes sur N requêtes |
| **Coût** | Dépense API | tokens entrée + sortie × tarif ; par session ou par jour |
| **Exact match / F1** | Réponse identique ou chevauchement de tokens | Utile surtout pour FAQ à réponse courte ; rare en RAG conversationnel |

#### Workflow recommandé

1. Constituer un **golden set** sur vos documents réels.
2. Exécuter le pipeline (config A vs config B).
3. Calculer **Recall@k / MRR** (retrieval) et **faithfulness** (génération).
4. Ne déployer en prod qu'après gain mesuré ou validation humaine."""
    ),
]

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "pygments_lexer": "ipython3",
        },
    },
    "cells": cells,
}

NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote {NOTEBOOK} ({len(cells)} cells)")
