# Notebook de présentation RAG

Notebook pas-à-pas pour expliquer l'ingestion, le chunking, les embeddings, le retrieval et la génération — avec **embeddings locaux** et **génération via Vercel AI Gateway**.

## Prérequis

Suivre [**SETUP.md**](../SETUP.md) à la racine du dépôt (Mac, Homebrew, **VS Code**, venv **`.venv-notebook`**, Python **3.11**).

1. Stack installée selon `SETUP.md` (CLT, Homebrew, `python@3.11`, VS Code + extensions Python / Jupyter).
2. `pip install -r notebooks/requirements-notebook.txt` dans `.venv-notebook` (fichier **autonome**, sans `backend/requirements.txt`).
3. Fichier `.env` à la racine avec **`VERCEL_AI_GATEWAY_KEY`** pour la section 7. Modèle atelier : **`WORKSHOP_ANSWER_MODEL_KEY`** = `"llama-3.2"` ou `"mistral-3b"`.

## Installation rapide (rappel)

```bash
cd rag-from-scratch-workshop
python3.11 -m venv .venv-notebook
source .venv-notebook/bin/activate
pip install -r notebooks/requirements-notebook.txt
python -m ipykernel install --user --name rag-workshop --display-name "RAG Workshop"
cp .env.example .env   # puis renseigner VERCEL_AI_GATEWAY_KEY
```

Ouvrir [`rag_atelier_presentation.ipynb`](rag_atelier_presentation.ipynb) dans **VS Code** et sélectionner le kernel **RAG Workshop** ou `.venv-notebook`.

## Démo interactive

1. Copiez **votre PDF** dans [`data/samples/`](../data/samples/).
2. Configurez `.env` (clé Gateway) ; en **section 7**, choisissez `WORKSHOP_ANSWER_MODEL_KEY` (`llama-3.2` ou `mistral-3b`).
3. Dans VS Code, exécutez les cellules dans l'ordre (ou *Run All*).
4. Laissez `DEMO_FILENAME = None` pour le premier PDF du dossier, ou précisez le nom du fichier.
5. Adaptez `DEMO_QUESTION` pour interroger votre document.

Voir aussi [`data/samples/README.md`](../data/samples/README.md).

Les DataFrames sont affichés avec `show()` ([itables](https://github.com/mwouts/itables)) : tri, recherche et pagination dans le notebook.

## Parcours du notebook

1. PDF → extraction → chunking → embeddings → indexation Chroma
2. Retrieval (`VECTOR_TOP_K` chunks)
3. Génération **sans RAG** vs **avec RAG** (Gateway)
4. Agent routeur (amélioration multi-sources)
5. Synthèse et pistes (rerank, filtre filename, etc.)

## Fichiers générés (gitignored)

- `data/notebook_chroma/` — index Chroma du notebook
- `data/notebook_knowledge.db` — SQLite de démo du notebook

## Parallèle avec l'application

| Notebook | Application (`docker compose`) |
|----------|--------------------------------|
| sentence-transformers | Vercel AI Gateway + `EMBEDDING_MODEL` |
| retrieval direct top_k | + rerank / diversification en prod |
| Gateway `WORKSHOP_ANSWER_MODEL` (Llama / Mistral) | `ANSWER_MODEL` du `.env` (streaming SSE) |
| heuristic_route (§8) | LLM routeur si clé Gateway |

## Régénérer le notebook

```bash
python3 notebooks/build_notebook.py
```
