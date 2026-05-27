# Dossier de démonstration — vos fichiers

Placez ici **le PDF que vous voulez analyser** pendant le notebook de présentation RAG.

## Instructions atelier

1. Copiez un ou plusieurs fichiers `.pdf` dans ce dossier.
2. Dans le notebook : `DEMO_FILENAME = None` prend le **premier PDF** (ordre alphabétique), ou indiquez le nom exact (`"mon_rapport.pdf"`).
2. Ouvrez `notebooks/rag_atelier_presentation.ipynb` et exécutez les cellules.
3. Le notebook détectera le type, extraira le texte (ou lancera l'OCR si nécessaire), chunkera, indexera et répondra à votre question.

Le fichier `example.csv` illustre des **KPI par centre DermaScan** (chiffre d'affaires, patients, consultations, mélanomes détectés, médecins) pour la branche SQL lorsque le document principal n'est pas tabulaire (ex. PDF).
