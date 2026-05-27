# rag-workshop

Assistant IA RAG multi-source construit pour un workshop d'entreprise, avec ingestion de documents `PDF/PNG/JPG/WEBP/CSV/XLSX`, extraction PDF `pdfplumber` + fallback OCR `DocTR`, stockage dual `SQLite + ChromaDB`, routage automatique `SQL / VECTOR / BOTH` et pile de modèles servie via `Vercel AI Gateway`.

## Démarrage rapide

1. Copier la configuration d'environnement :

```bash
cp .env.example .env
```

2. Renseigner `VERCEL_AI_GATEWAY_KEY` dans `.env`.
3. Lancer l'application :

```bash
docker compose up --build
```

4. Ouvrir `http://localhost:3001`.

## Ce que fait le projet

- Upload de documents et d'images depuis l'interface.
- OCR DocTR automatique pour les images et pour les PDF sans couche texte.
- Indexation automatique dans une base vectorielle persistée.
- Stockage des données tabulaires dans SQLite.
- Chat avec streaming token par token.
- Badge indiquant si la réponse provient d'un flux `SQL`, `VECTOR` ou `BOTH`.
- Sources utilisees affichees sous chaque reponse du chat.
- Reindexation d'un document depuis son fichier source quand la collection vectorielle active change.

## Structure

- `backend/` : API FastAPI, ingestion, embeddings, stores et agent.
- `frontend/` : interface Next.js.
- `data/` : bases persistées et jeux de données d'exemple.
- `scripts/` : petits supports pédagogiques.

## Données d'exemple

Le dépôt contient des fichiers dans `data/samples/` pour tester immédiatement l'upload et le routage.

## Notebook de présentation RAG

Pour une démo pas-à-pas du pipeline (ingestion → retrieval → génération), voir [`notebooks/rag_atelier_presentation.ipynb`](notebooks/rag_atelier_presentation.ipynb) et [`notebooks/README.md`](notebooks/README.md). Déposez votre document dans `data/samples/` avant d'exécuter le notebook.

## Notes d'exploitation

- Les données indexées sont persistées dans `data/knowledge.db` et `data/chroma_db/`.
- Les fichiers sources reindexables sont persistés dans `data/source_documents/`.
- L'ajout ou la suppression de documents se fait depuis l'onglet `Knowledge`.
- La reindexation rejoue le fichier source dans la collection Chroma active du modèle d'embedding courant.
- Sans clé `VERCEL_AI_GATEWAY_KEY`, ni le chat ni les embeddings distants ne pourront etre executes.
- La pile par defaut utilise `google/gemini-3.1-flash-lite` pour le routage, `openai/gpt-4o-mini` pour la generation et `alibaba/qwen3-embedding-4b` pour les embeddings, avec `VECTOR_TOP_K=10`.
- Les appels Gateway sont effectues avec `zeroDataRetention: true`; selon le plan ou les providers disponibles, cette contrainte peut rendre certains appels indisponibles.
- Les appels Gateway appliquent un retry/backoff sur les erreurs `429` (`GATEWAY_MAX_RETRIES`, `GATEWAY_MAX_RETRY_DELAY_SECONDS`). L'ingestion decoupe les embeddings par lots (`EMBEDDING_BATCH_SIZE`, `EMBEDDING_BATCH_DELAY_SECONDS`). Un quota free tier durablement epuise peut toutefois bloquer l'upload : attendez quelques minutes ou ajoutez des credits Vercel.
- Si vous migrez depuis un ancien modèle d'embedding, la collection active change. Les documents historiques sans fichier source persiste devront etre re-uploadés une fois pour redevenir reindexables.
- Après une évolution du pipeline d'ingestion (métadonnées `document_kind`, découpage par sections), re-uploadez ou reindexez les documents existants depuis l'onglet `Knowledge` pour régénérer les chunks en base.
