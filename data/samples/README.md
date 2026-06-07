# Dossier de démonstration — vos fichiers

Placez ici **le PDF que vous voulez analyser** pendant le notebook de présentation RAG.

## Fichier fourni

Le dépôt inclut [`DermaScan_fiche_projet_demo.pdf`](DermaScan_fiche_projet_demo.pdf), un **document fictif** (données simulées) décrivant un réseau de centres de dermatologie et un projet IA dermoscopique. Il sert de corpus par défaut pour l'atelier RAG — aucune donnée réelle de patient ni information contractuelle.

Pour régénérer ce PDF : `python scripts/generate_dermascan_sample_pdf.py` (source Markdown dans [`_sources/dermascan_demo_content.md`](_sources/dermascan_demo_content.md)).

## Instructions atelier

1. Copiez un ou plusieurs fichiers `.pdf` dans ce dossier.
2. Dans le notebook : `DEMO_FILENAME = None` prend le **premier PDF** (ordre alphabétique), ou indiquez le nom exact (`"mon_rapport.pdf"`).
2. Ouvrez `notebooks/rag_atelier_presentation.ipynb` et exécutez les cellules.
3. Le notebook détectera le type, extraira le texte (ou lancera l'OCR si nécessaire), chunkera, indexera et répondra à votre question.

Le fichier `example.csv` illustre des **KPI par centre DermaScan** (chiffre d'affaires, patients, consultations, mélanomes détectés, médecins) pour la branche SQL lorsque le document principal n'est pas tabulaire (ex. PDF).
