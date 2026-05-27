# Notebook de présentation RAG

Notebook pas-à-pas pour expliquer l'ingestion, le chunking, les embeddings, le retrieval et la génération — avec **embeddings locaux** et **génération via Vercel AI Gateway**.

## Prérequis

1. Environnement Python **3.9+** (3.11+ recommandé, aligné sur le Docker backend).
2. Dépendances backend installées (`pip install -r backend/requirements.txt`).
3. Dépendances notebook (`pip install -r notebooks/requirements-notebook.txt`, inclut **itables** pour les tableaux interactifs).
4. Fichier `.env` à la racine avec **`VERCEL_AI_GATEWAY_KEY`**. Le modèle atelier est choisi **en section 7** via **`WORKSHOP_ANSWER_MODEL_KEY`** : `"llama-3.2"` ou `"mistral-3b"` (indépendant de `ANSWER_MODEL` en production).

## Installation rapide

```bash
cd /chemin/vers/rag-from-scratch-workshop
python -m venv .venv-notebook
source .venv-notebook/bin/activate
pip install -r backend/requirements.txt
pip install -r notebooks/requirements-notebook.txt
python -m ipykernel install --user --name rag-workshop --display-name "RAG Workshop"
```

## Démo interactive

1. Copiez **votre PDF** dans [`data/samples/`](../data/samples/).
2. Configurez `.env` (clé Gateway) ; en **section 7**, choisissez `WORKSHOP_ANSWER_MODEL_KEY` (`llama-3.2` ou `mistral-3b`).
3. Lancez Jupyter : `jupyter lab notebooks/rag_atelier_presentation.ipynb`
4. Exécutez les cellules dans l'ordre (ou *Run All* après avoir déposé le fichier).
5. Laissez `DEMO_FILENAME = None` pour le premier PDF du dossier, ou précisez le nom du fichier.
6. Adaptez `DEMO_QUESTION` pour interroger votre document.

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
