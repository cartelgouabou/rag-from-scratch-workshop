# 📋 Cahier des Charges — Projet `rag-workshop`

> Assistant IA RAG multi-source avec agent de routage SQL / Vector
> Atelier pratique de 40 minutes — Profils mixtes

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Structure du repo](#2-structure-du-repo)
3. [Prérequis & Installation](#3-prérequis--installation)
4. [Backend — Spécifications](#4-backend--spécifications)
5. [Frontend — Spécifications](#5-frontend--spécifications)
6. [API — Contrat d'interface](#6-api--contrat-dinterface)
7. [Variables d'environnement](#7-variables-denvironnement)
8. [Plan de l'atelier pratique](#8-plan-de-latelier-pratique)
9. [Décisions d'architecture](#9-décisions-darchitecture)

---

## 1. Vue d'ensemble

| Attribut | Valeur |
|---|---|
| Nom du projet | `rag-workshop` |
| Objectif | RAG multi-source avec agent de routage SQL / Vector |
| Durée pratique | 40 min guidées |
| Public cible | Profils mixtes (dev, data, métier) |
| Backend | Python 3.11+ |
| Frontend | TypeScript / Next.js 14 |
| Déploiement | Local (VS Code + localhost) |

### Fonctionnalités principales

- **Ingestion** de fichiers PDF, CSV et Excel dans une base de connaissance duale (SQLite + ChromaDB)
- **Chat** en langage naturel avec streaming token par token
- **Agent de routage** qui décide automatiquement d'interroger la base SQL ou la base vectorielle selon la question
- **Dashboard** listant les documents indexés avec leurs statistiques
- **Gestion** de la base de connaissance : ajout et suppression de documents depuis l'interface

---

## 2. Structure du repo

```
rag-workshop/
├── README.md                        ← Ce fichier
├── README_PRESENTATION.md           ← Support théorique (10 min)
├── .env.example                     ← Template des variables d'environnement
│
├── backend/
│   ├── main.py                      ← Point d'entrée FastAPI + CORS
│   ├── config.py                    ← Paramètres centralisés (depuis .env)
│   ├── requirements.txt
│   │
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── loader.py                ← Lecture PDF (PyMuPDF), CSV, Excel (Pandas)
│   │   ├── chunker.py               ← RecursiveCharacterTextSplitter (LangChain)
│   │   └── embedder.py              ← sentence-transformers, batch processing
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── vector_store.py          ← Interface ChromaDB (add, query, delete)
│   │   └── sql_store.py             ← Interface SQLite + SQLAlchemy (CRUD)
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── router.py                ← Prompt de classification sql/vector
│   │   └── llm_client.py            ← Client Vercel AI Gateway (chat + stream)
│   │
│   └── api/
│       ├── __init__.py
│       ├── routes_ingest.py         ← POST /api/ingest/upload
│       ├── routes_chat.py           ← POST /api/chat  (SSE streaming)
│       └── routes_knowledge.py      ← GET/DELETE /api/knowledge/...
│
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── .env.local.example
│   │
│   └── src/
│       ├── app/
│       │   ├── layout.tsx           ← Layout global + navigation onglets
│       │   ├── page.tsx             ← Onglet 1 : Dashboard + Chat
│       │   └── knowledge/
│       │       └── page.tsx         ← Onglet 2 : Gestion base de connaissance
│       │
│       ├── components/
│       │   ├── Chat/
│       │   │   ├── ChatWindow.tsx   ← Conteneur de la conversation
│       │   │   ├── MessageBubble.tsx← Bulle user / assistant
│       │   │   └── SourceBadge.tsx  ← Badge "SQL" ou "VECTOR"
│       │   │
│       │   ├── Dashboard/
│       │   │   ├── StatsCards.tsx   ← Cartes : nb docs, chunks, entrées SQL
│       │   │   └── KnowledgeTable.tsx ← Liste des documents indexés
│       │   │
│       │   └── Knowledge/
│       │       ├── FileUploader.tsx  ← Drag & drop (react-dropzone)
│       │       └── DocumentList.tsx  ← Tableau avec bouton suppression
│       │
│       └── lib/
│           └── api.ts               ← Client HTTP centralisé (fetch + SSE)
│
├── data/
│   ├── chroma_db/                   ← Base vectorielle persistée (gitignored)
│   ├── knowledge.db                 ← Base SQLite (gitignored)
│   └── samples/
│       ├── example.pdf              ← Jeu de données exemple
│       ├── example.csv
│       └── example.xlsx
│
└── scripts/
    └── embed_demo.py                ← Script pédagogique : visualise la similarité cosinus
```

---

## 3. Prérequis & Installation

### Prérequis participants

| Outil | Version minimale | Lien |
|---|---|---|
| VS Code | Dernière version | https://code.visualstudio.com |
| Python | 3.11+ | https://python.org |
| Node.js | 18+ | https://nodejs.org |
| Git | Toute version récente | https://git-scm.com |

### Installation complète

```bash
# 1. Cloner le repo
git clone https://github.com/<username>/rag-workshop.git
cd rag-workshop

# 2. Backend
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt

# 3. Variables d'environnement backend
cp ../.env.example ../.env
# → Éditer .env et renseigner VERCEL_API_KEY_RAG_WORKSHOP

# 4. Frontend
cd ../frontend
npm install
cp .env.local.example .env.local

# 5. Lancer le backend
cd ../backend
uvicorn main:app --reload --port 8000

# 6. Lancer le frontend (dans un second terminal)
cd ../frontend
npm run dev
# → Ouvrir http://localhost:3000
```

---

## 4. Backend — Spécifications

### 4.1 Stack technique

| Composant | Outil | Version | Justification |
|---|---|---|---|
| Framework API | **FastAPI** | 0.111+ | Standard industrie, async natif, Swagger auto |
| Ingestion PDF | **PyMuPDF** (`fitz`) | 1.24+ | Rapide, gère les PDF complexes, open source |
| Ingestion CSV/Excel | **Pandas** | 2.x | Universel, robuste, très répandu |
| Chunking | **LangChain** `RecursiveCharacterTextSplitter` | 0.2+ | Stratégie de split la plus efficace en pratique |
| Embedding | **sentence-transformers** `all-MiniLM-L6-v2` | 3.x | Local, gratuit, 80MB, ~14k phrases/sec sur CPU |
| Vector DB | **ChromaDB** | 0.5+ | Embarqué, persistant, zéro infra |
| SQL DB | **SQLite** + **SQLAlchemy** | — | Zéro infra, fichier local, ORM propre |
| LLM Gateway | **Vercel AI Gateway** | — | Abstraction multi-provider, une seule clé |
| Validation | **Pydantic v2** | 2.x | Intégré FastAPI, typage fort |
| CORS | FastAPI middleware | — | Autorise le frontend localhost:3000 |

### 4.2 Pipeline d'ingestion détaillé

```
Fichier uploadé (PDF / CSV / Excel)
        │
        ▼
┌───────────────────────────────────────┐
│  1. Détection du type                 │
│     • Extension + magic bytes         │
│     • Types supportés : .pdf .csv     │
│       .xlsx .xls                      │
└──────────────┬────────────────────────┘
               │
       ┌───────┴────────┐
      PDF          CSV / Excel
       │                │
       ▼                ▼
  PyMuPDF           Pandas
  texte page      chaque ligne =
  par page        une entrée SQL
       │          + texte pour embed
       └───────┬────────┘
               │
               ▼
┌───────────────────────────────────────┐
│  2. Chunking                          │
│     chunk_size    = 500 tokens        │
│     chunk_overlap = 50 tokens         │
│     séparateurs   = ["\n\n","\n"," "] │
└──────────────┬────────────────────────┘
               │
               ▼
┌───────────────────────────────────────┐
│  3. Embedding (batch de 32 chunks)    │
│     Modèle : all-MiniLM-L6-v2        │
│     Dimensions : 384                  │
└──────────────┬────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
  ChromaDB           SQLite
  chunks +          metadata du doc
  embeddings        + données tabulaires
  + metadata        (CSV/Excel)
       │                │
       └───────┬────────┘
               ▼
  Retour : { document_id, nb_chunks, duration_ms }
```

### 4.3 Agent de routage

L'agent effectue un seul appel LLM léger (`max_tokens=5`) pour classer la question.

**Prompt système de l'agent routeur :**

```
Tu es un agent de routage. Analyse la question et réponds UNIQUEMENT
par "sql" ou "vector" — aucun autre mot.

Règles de décision :
  "sql"    → question sur des données chiffrées, filtres, agrégations,
             dates précises, comptages, colonnes spécifiques
             Exemples : "Quel est le CA de mars ?",
                        "Combien de commandes en 2024 ?",
                        "Liste les lignes où statut = livré"

  "vector" → question sémantique, recherche de concepts, résumés,
             reformulations, questions ouvertes sur des documents
             Exemples : "Quels projets parlent de durabilité ?",
                        "Résume le rapport Q1",
                        "Quelles sont les recommandations ?"

Question : {question}
Réponse :
```

**Flux de décision dans `router.py` :**

```python
async def route(question: str) -> Literal["sql", "vector"]:
    response = await llm_client.complete(
        system=ROUTER_PROMPT,
        user=question,
        max_tokens=5,
        temperature=0
    )
    decision = response.strip().lower()
    return "sql" if "sql" in decision else "vector"
```

### 4.4 `requirements.txt`

```txt
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
python-multipart>=0.0.9
pydantic>=2.7.0
pydantic-settings>=2.3.0

# Ingestion
pymupdf>=1.24.0
pandas>=2.2.0
openpyxl>=3.1.0
xlrd>=2.0.0

# Chunking & Embedding
langchain-text-splitters>=0.2.0
sentence-transformers>=3.0.0

# Vector DB
chromadb>=0.5.0

# SQL
sqlalchemy>=2.0.0

# HTTP client (LLM Gateway)
httpx>=0.27.0
```

---

## 5. Frontend — Spécifications

### 5.1 Stack technique

| Composant | Outil | Version | Justification |
|---|---|---|---|
| Framework | **Next.js** (App Router) | 14+ | Standard, SSR, routing simple |
| Langage | **TypeScript** | 5.x | Typage fort, détection d'erreurs |
| UI Components | **shadcn/ui** | Dernière | Open source, copiable, Tailwind-based |
| Styling | **Tailwind CSS** | 3.x | Productivité, cohérence visuelle |
| Icônes | **Lucide React** | 0.38x | Cohérent avec shadcn, open source |
| Requêtes HTTP | **SWR** + `fetch` natif | 2.x | Revalidation auto, cache |
| Upload | **react-dropzone** | 14.x | Drag & drop robuste, très répandu |
| Streaming | **EventSource API** | natif | Affichage token par token sans dépendance |

### 5.2 Onglet 1 — Dashboard + Chat

```
┌─────────────────────────────────────────────────────────┐
│  🤖 RAG Workshop               [Dashboard] [Knowledge]  │
├──────────────────────┬──────────────────────────────────┤
│  BASE DE CONNAISSANCE│  CHAT                            │
│                      │                                  │
│  📊 Statistiques     │  ┌────────────────────────────┐  │
│  ┌────────────────┐  │  │ 🤖 Assistant               │  │
│  │ 📄 12 documents│  │  │ Bonjour ! Posez-moi une    │  │
│  │ 🧩 847 chunks  │  │  │ question sur vos documents.│  │
│  │ 🗄️ 1204 lignes │  │  └────────────────────────────┘  │
│  └────────────────┘  │                                  │
│                      │  ┌────────────────────────────┐  │
│  📁 Documents        │  │ 👤 Vous                    │  │
│  ┌────────────────┐  │  │ Quel est le total des      │  │
│  │📄 rapport.pdf  │  │  │ ventes en mars ?           │  │
│  │📊 ventes.csv   │  │  └────────────────────────────┘  │
│  │📋 planning.xlsx│  │                                  │
│  └────────────────┘  │  ┌────────────────────────────┐  │
│                      │  │ 🤖 Assistant    [🗄️ SQL]   │  │
│                      │  │ Le total des ventes en mars │  │
│                      │  │ est de 142 300 €...         │  │
│                      │  └────────────────────────────┘  │
│                      │                                  │
│                      │  ┌──────────────────────┐[Send]  │
│                      │  │ Posez votre question…│        │
│                      │  └──────────────────────┘        │
└──────────────────────┴──────────────────────────────────┘
```

**Comportements attendus :**
- Le panel gauche se rafraîchit automatiquement après chaque upload
- Le chat supporte le **streaming SSE** (affichage progressif des tokens)
- Chaque réponse affiche un badge **`🗄️ SQL`** ou **`🔍 VECTOR`** indiquant la source utilisée
- L'historique de conversation est conservé pendant la session

### 5.3 Onglet 2 — Gestion de la base de connaissance

```
┌─────────────────────────────────────────────────────────┐
│  [Dashboard] [Knowledge ●]                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  AJOUTER DES DONNÉES                                    │
│  ┌───────────────────────────────────────────────────┐  │
│  │                                                   │  │
│  │         📂 Glissez vos fichiers ici               │  │
│  │      ou cliquez pour sélectionner                 │  │
│  │                                                   │  │
│  │      Formats : PDF, CSV, Excel — Max 20 MB        │  │
│  │                                                   │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │ ✅ rapport_q1.pdf — 847 Ko   [Indexation...  67%]│   │
│  └──────────────────────────────────────────────────┘   │
│  [Uploader les fichiers sélectionnés]                   │
│                                                         │
│  DOCUMENTS INDEXÉS                      [🔄 Actualiser] │
│  ┌──────┬────────────────┬────────┬──────────┬───────┐  │
│  │ Type │ Nom            │ Chunks │ Indexé le │ Action│  │
│  ├──────┼────────────────┼────────┼──────────┼───────┤  │
│  │ PDF  │ rapport_q1.pdf │  124   │ 21/05/26  │ [🗑️] │  │
│  │ CSV  │ ventes_2024.csv│   89   │ 20/05/26  │ [🗑️] │  │
│  │ XLSX │ planning.xlsx  │   67   │ 20/05/26  │ [🗑️] │  │
│  └──────┴────────────────┴────────┴──────────┴───────┘  │
└─────────────────────────────────────────────────────────┘
```

**Comportements attendus :**
- Upload multi-fichiers simultanés
- Barre de progression par fichier pendant l'ingestion
- Confirmation avant suppression d'un document
- La suppression retire le document de ChromaDB ET de SQLite

---

## 6. API — Contrat d'interface

### Endpoints Backend

#### `POST /api/ingest/upload`
Upload et ingestion d'un fichier.

```
Request  : multipart/form-data  { file: File }
Response : {
  "document_id": "uuid-...",
  "filename": "rapport.pdf",
  "type": "pdf",
  "nb_chunks": 124,
  "nb_records": 0,
  "duration_ms": 3420
}
Erreurs  : 400 (type non supporté), 413 (fichier trop grand), 500
```

#### `GET /api/knowledge/documents`
Liste tous les documents indexés.

```
Response : {
  "documents": [
    {
      "id": "uuid-...",
      "filename": "rapport.pdf",
      "type": "pdf",
      "nb_chunks": 124,
      "nb_records": 0,
      "indexed_at": "2026-05-21T14:30:00Z"
    }
  ],
  "stats": {
    "total_documents": 3,
    "total_chunks": 280,
    "total_records": 1204
  }
}
```

#### `DELETE /api/knowledge/documents/{document_id}`
Suppression d'un document (ChromaDB + SQLite).

```
Response : { "success": true, "document_id": "uuid-..." }
Erreurs  : 404 (document introuvable)
```

#### `POST /api/chat`
Envoi d'un message — réponse en streaming SSE.

```
Request  : { "message": "Quel est le CA de mars ?", "history": [...] }

Response : text/event-stream
  data: {"type": "routing", "decision": "sql"}
  data: {"type": "token", "content": "Le"}
  data: {"type": "token", "content": " total"}
  data: {"type": "token", "content": " des"}
  ...
  data: {"type": "done", "source": "sql", "chunks_used": 0}
```

#### `GET /api/knowledge/stats`
Statistiques globales de la base de connaissance.

```
Response : {
  "total_documents": 3,
  "total_chunks": 280,
  "total_records": 1204,
  "chroma_size_mb": 12.4,
  "sqlite_size_mb": 0.8
}
```

---

## 7. Variables d'environnement

### Backend — `.env`

```bash
# Vercel AI Gateway
VERCEL_AI_GATEWAY_URL=https://ai-gateway.vercel.sh/v1
VERCEL_API_KEY_RAG_WORKSHOP=your_key_here
LLM_MODEL=openai/gpt-4o-mini        # ou anthropic/claude-haiku-4-5

# Embedding (local, pas de clé nécessaire)
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Stockage
CHROMA_PATH=./data/chroma_db
SQLITE_PATH=./data/knowledge.db

# Chunking
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# Upload
MAX_UPLOAD_SIZE_MB=20

# CORS
FRONTEND_URL=http://localhost:3000
```

### Frontend — `.env.local`

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 8. Plan de l'atelier pratique

### Déroulé détaillé (40 min)

| # | Étape | Durée | Ce que les participants font | Fichiers concernés |
|---|---|---|---|---|
| 0 | **Setup** | 5 min | `git clone`, install backend + frontend, copier `.env` | `requirements.txt`, `package.json` |
| 1 | **Explorer l'ingesteur** | 8 min | Lire `loader.py` + `chunker.py`, lancer le script démo, observer les chunks produits | `ingestion/loader.py`, `ingestion/chunker.py` |
| 2 | **Visualiser les embeddings** | 5 min | Lancer `scripts/embed_demo.py`, observer la similarité cosinus entre 3 phrases, comprendre la notion de proximité sémantique | `scripts/embed_demo.py` |
| 3 | **Backend + Swagger** | 5 min | `uvicorn main:app --reload`, ouvrir `/docs`, uploader `data/samples/example.pdf` via Swagger | `main.py`, `api/routes_ingest.py` |
| 4 | **Tester l'agent routeur** | 7 min | Via Swagger, envoyer une question SQL et une question sémantique, observer le badge de routage dans la réponse SSE | `agent/router.py` |
| 5 | **Frontend** | 5 min | `npm run dev`, explorer les 2 onglets, uploader un fichier via l'UI | Tous les composants |
| 6 | **Démo libre** | 5 min | Chacun uploade ses propres fichiers et teste des questions personnalisées | — |

### Script `embed_demo.py` (contenu pédagogique)

```python
"""
Démo : visualiser la similarité sémantique entre phrases
Lancer : python scripts/embed_demo.py
"""
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

phrases = [
    "Les ventes ont augmenté en mars",
    "Le chiffre d'affaires de mars est en hausse",
    "La météo est nuageuse aujourd'hui",
]

embeddings = model.encode(phrases)

print("\n=== Similarité cosinus entre les phrases ===\n")
for i in range(len(phrases)):
    for j in range(i + 1, len(phrases)):
        sim = cosine_similarity([embeddings[i]], [embeddings[j]])[0][0]
        print(f"  [{i+1}] vs [{j+1}] : {sim:.3f}")
        print(f"        '{phrases[i][:50]}'")
        print(f"        '{phrases[j][:50]}'")
        print()

# Attendu :
# [1] vs [2] : ~0.85  (proches sémantiquement)
# [1] vs [3] : ~0.10  (sans rapport)
# [2] vs [3] : ~0.08  (sans rapport)
```

---

## 9. Décisions d'architecture

| Décision | Choix retenu | Alternative écartée | Raison |
|---|---|---|---|
| **Vector DB** | ChromaDB embarqué | Qdrant, Weaviate, Pinecone | Zéro serveur, parfait pour atelier local |
| **Embedding** | sentence-transformers (local) | OpenAI `text-embedding-3-small` | Gratuit, fonctionne offline, pas de latence réseau |
| **LLM** | Vercel AI Gateway | Appels directs OpenAI / Anthropic | Une seule clé API pour tous les participants, multi-provider |
| **SQL DB** | SQLite | PostgreSQL, MySQL | Zéro infra, fichier local, suffisant pour l'atelier |
| **Chunking** | LangChain `RecursiveCharacterTextSplitter` | Chunking fixe naïf | Respecte la structure naturelle du texte |
| **Frontend** | Next.js 14 App Router | React Vite, Vue | Routing natif pour les 2 onglets, plus structuré |
| **Streaming** | SSE (Server-Sent Events) | WebSocket | Plus simple à implémenter côté backend et frontend |
| **Agent** | LLM avec prompt de classification | Classificateur ML custom | Pas de dataset d'entraînement requis, flexible |
| **Upload** | react-dropzone | Input file natif HTML | UX drag & drop, gestion multi-fichiers intégrée |

---

## Annexe — Données d'exemple recommandées

Pour l'atelier, préparer 3 fichiers dans `data/samples/` :

| Fichier | Contenu suggéré | Permet de tester |
|---|---|---|
| `example.pdf` | Rapport d'activité fictif (2-3 pages) | Routing VECTOR, résumé, extraction de concepts |
| `example.csv` | Données de ventes mensuelles (12 lignes) | Routing SQL, agrégations, filtres |
| `example.xlsx` | Planning de projets avec dates et statuts | Routing SQL et VECTOR selon la question |

---

*Cahier des charges — Atelier RAG — Arthur Cartel Foahom Gouabou*
*Lead AI Engineer & Chercheur en IA — Marseille, France*
