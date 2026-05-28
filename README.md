# rag-from-scratch-workshop

Assistant IA **RAG multi-source** pour un atelier d'entreprise : ingestion `PDF / images / CSV / Excel`, extraction PDF (`pdfplumber` + OCR `DocTR`), stockage **SQLite + ChromaDB**, routage `SQL | VECTOR | BOTH`, modèles via **Vercel AI Gateway**.

## Démarrage rapide (application)

1. Copier la configuration :

```bash
cp .env.example .env
```

2. Renseigner `VERCEL_AI_GATEWAY_KEY` dans `.env`.
3. Lancer :

```bash
docker compose up --build
```

4. Ouvrir [http://localhost:3001](http://localhost:3001).

## Atelier notebook (recommandé en salle)

Parcours pas-à-pas **sans Docker** pour le pipeline RAG sur un PDF : [`notebooks/rag_atelier_presentation.ipynb`](notebooks/rag_atelier_presentation.ipynb).

| Étape | Contenu |
|-------|---------|
| 1–5 | PDF → extraction → chunking → embeddings locaux → indexation Chroma |
| 6 | Retrieval (`VECTOR_TOP_K`, distance L2) |
| 7 | Génération **sans RAG** / **avec RAG** (Gateway) |
| 8 | Agent routeur (amélioration multi-sources) |
| 9 | Synthèse et pistes d'évolution |

**Installation notebook (Mac)** — [**SETUP.md**](SETUP.md) : clone ou ZIP → [`./setup-mac.sh`](setup-mac.sh) (Homebrew, Python 3.11, VS Code, Docker Desktop, venv `.venv-notebook`).

```bash
cd rag-from-scratch-workshop
./setup-mac.sh
```

Puis ouvrir dans **VS Code** : [`notebooks/rag_atelier_presentation.ipynb`](notebooks/rag_atelier_presentation.ipynb).

- Déposez un PDF dans [`data/samples/`](data/samples/) (un exemple DermaScan est fourni).
- Section **7** : choisir `WORKSHOP_ANSWER_MODEL_KEY` = `"llama-3.2"` (`meta/llama-3.2-3b`) ou `"mistral-3b"` (`mistral/ministral-3b`) — distinct de `ANSWER_MODEL` en production.
- Deux cellules de génération avec pause anti-429 (free tier Gateway).

Régénérer le `.ipynb` depuis la source :

```bash
python3 notebooks/build_notebook.py
```

## Ce que fait l'application

- Upload de documents et d'images depuis l'interface.
- OCR DocTR pour images et PDF sans texte extractible.
- Indexation vectorielle (Chroma) et tables SQL (CSV/Excel).
- Chat en streaming avec badge de route (`SQL`, `VECTOR`, `BOTH`) et sources citées.
- Reindexation depuis le fichier source lors d'un changement de modèle d'embedding.

## Structure du dépôt

| Dossier | Rôle |
|---------|------|
| [`backend/`](backend/) | API FastAPI, ingestion, embeddings Gateway, stores, agent |
| [`frontend/`](frontend/) | Interface Next.js |
| [`notebooks/`](notebooks/) | Atelier Jupyter (`build_notebook.py` → `.ipynb`) |
| [`data/samples/`](data/samples/) | PDF/CSV de démo pour le notebook |
| [`scripts/`](scripts/) | Utilitaires pédagogiques |

Données **non versionnées** (voir [`.gitignore`](.gitignore)) : `.env`, `.venv-notebook/`, `backend/.venv/`, `data/chroma_db/`, `data/notebook_chroma/`, bases SQLite, `data/source_documents/`, PDFs à la racine du repo.

## Configuration (`.env`)

| Variable | Usage |
|----------|--------|
| `VERCEL_AI_GATEWAY_KEY` | Chat, embeddings prod, notebook §7 |
| `ANSWER_MODEL` | Génération application (ex. `openai/gpt-4o-mini`) |
| `EMBEDDING_MODEL` | Embeddings application |
| `ROUTER_MODEL` | Routeur LLM si clé configurée |
| `VECTOR_TOP_K` | Nombre de chunks retrieval (défaut `10`) |

Sans clé Gateway : le chat et les embeddings distants de l'app ne fonctionnent pas ; le notebook reste utilisable pour les étapes 1–6 (embeddings locaux `sentence-transformers`).

## Données d'exemple

- [`data/samples/Dossier_CIFRE_DermaScan_draft_v3.pdf`](data/samples/Dossier_CIFRE_DermaScan_draft_v3.pdf) — PDF atelier
- [`data/samples/example.csv`](data/samples/example.csv) — KPI centres (branche SQL de l'app, hors notebook PDF)

## Notes d'exploitation

- Persistance app : `data/knowledge.db`, `data/chroma_db/`, `data/source_documents/`.
- Gateway : `zeroDataRetention: true`, retries sur `429` (`GATEWAY_MAX_RETRIES`, `GATEWAY_MAX_RETRY_DELAY_SECONDS`).
- Ingestion : lots d'embeddings (`EMBEDDING_BATCH_SIZE`, `EMBEDDING_BATCH_DELAY_SECONDS`). Quota free tier : prévoir une pause entre appels LLM (notebook §7).
- Après changement de `EMBEDDING_MODEL` ou du pipeline de chunking : re-uploader ou reindexer depuis l'onglet **Knowledge**.
