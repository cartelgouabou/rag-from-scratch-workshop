# Support théorique

Ce dépôt accompagne un workshop RAG construit en deux temps :

1. `Indexation`
   - chargement des documents,
   - découpage en chunks,
   - génération d'embeddings,
   - stockage dans SQLite et ChromaDB.

2. `Retrieval + Generation`
   - l'utilisateur pose une question,
   - un agent route la question vers `sql` ou `vector`,
   - le backend récupère le bon contexte,
   - le LLM produit une réponse contextualisée.

## Concepts clés

- `Chunking` : découper un document en morceaux qui gardent du sens.
- `Embedding` : transformer du texte en vecteurs numériques.
- `Vector store` : retrouver les contenus les plus proches sémantiquement.
- `SQL store` : répondre aux questions tabulaires, aux filtres et aux agrégations.

## Objectif pédagogique

À la fin du workshop, chaque participant doit pouvoir :

- démarrer le projet via `docker compose up`,
- charger ses propres documents,
- discuter avec un assistant personnel basé sur sa propre base de connaissance.

## Notebook de présentation (pas à pas)

Le notebook [`notebooks/rag_atelier_presentation.ipynb`](notebooks/rag_atelier_presentation.ipynb) déroule le pipeline RAG **en direct** :

1. Déposez votre fichier dans [`data/samples/`](data/samples/).
2. Suivez ingestion, extraction/OCR, chunking, embeddings, similarité cosinus, index Chroma, SQL, retrieval, rerank, routage et génération.
3. Stack **open source** locale (sentence-transformers, flan-t5) avec encarts « équivalent backend » à chaque étape.

Installation : voir [`notebooks/README.md`](notebooks/README.md).
