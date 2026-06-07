# DermaScan — Fiche projet démonstration RAG

**Document fictif à des fins pédagogiques uniquement.** Toutes les entités, chiffres, personnes et organisations décrits ci-dessous sont simulés. Ce document ne constitue pas un dossier CIFRE, un contrat, ni une communication officielle.

**Version :** 1.0 — Atelier RAG multi-source  
**Date :** janvier 2025  
**Classification :** usage interne atelier / open source workshop

---

## 1. Présentation de DermaScan

DermaScan est un réseau fictif de centres de dermatologie préventive implanté dans six grandes agglomérations françaises. Fondé en 2018 dans le cadre d'un programme pilote de dépistage organisé des cancers cutanés, le réseau vise à rapprocher l'expertise dermatologique des populations à risque et à industrialiser un parcours de soins fondé sur l'imagerie numérique et l'aide à la décision.

La mission centrale de DermaScan consiste à détecter précocement les lésions suspectes — en particulier le mélanome et les carcinomes spinocellulaires — tout en réduisant les délais entre la première consultation et la confirmation histologique. Chaque centre combine une équipe médicale pluridisciplinaire (dermatologues, infirmières imagerie, data managers) et une plateforme numérique unifiée pour la collecte, l'annotation et le suivi des dossiers patients.

Le présent document décrit le projet de recherche et développement **DermaScan-AI**, une initiative visant à intégrer un module d'intelligence artificielle dans le flux de dermoscopie numérique. Ce projet s'inscrit dans la stratégie 2024–2027 du réseau et sert de corpus de démonstration pour les ateliers Retrieval-Augmented Generation (RAG).

---

## 2. Enjeux de santé publique

Le mélanome cutané représente en France environ 17 000 nouveaux cas par an et demeure responsable d'une mortalité significative lorsque le diagnostic intervient à un stade avancé (stades III et IV). La survie à cinq ans dépasse 95 % pour les mélanomes détectés précocement (stade I), contre moins de 30 % pour les formes métastatiques.

Les facteurs de risque majeurs incluent : antécédents personnels ou familiaux de mélanome, phototypes clairs (I–III), expositions solaires cumulées sans protection, et présence de nombreux naevus atypiques. Le dépistage organisé cible particulièrement les populations de 45 à 75 ans présentant au moins deux de ces facteurs.

DermaScan s'appuie sur trois piliers opérationnels :

1. **Accessibilité géographique** — des centres en zone urbaine dense pour limiter les ruptures de parcours.
2. **Standardisation des protocoles** — grilles communes d'examen clinique et de dermoscopie.
3. **Traçabilité numérique** — chaque image et chaque décision médicale est horodatée et référencée.

L'objectif quantitatif du réseau pour 2024 était de réaliser plus de 8 000 consultations de dépistage et de détecter au moins 130 lésions malignes confirmées par anatomopathologie.

---

## 3. Objectifs du projet DermaScan-AI

Le projet DermaScan-AI vise à concevoir, entraîner et déployer un assistant de classification des lésions cutanées à partir d'images dermoscopiques numériques. Les objectifs mesurables retenus pour la phase pilote (2024–2026) sont les suivants :

**Objectif 1 — Sensibilité diagnostique.** Atteindre une sensibilité ≥ 92 % sur la détection des mélanomes et des lésions à haut risque (score d'alerte élevé), mesurée sur un jeu de validation externe indépendant du corpus d'entraînement.

**Objectif 2 — Spécificité et réduction des biopsies inutiles.** Maintenir une spécificité ≥ 78 % pour limiter les sur-références en anatomopathologie, tout en conservant un taux de faux négatifs inférieur à 3 % sur les mélanomes confirmés.

**Objectif 3 — Délai de restitution.** Réduire de 40 % le délai médian entre la capture dermoscopique et la proposition de score d'alerte au dermatologue référent, en passant de 48 heures (revue manuelle seule) à moins de 24 heures avec le pipeline automatisé.

**Objectif 4 — Standardisation inter-centres.** Harmoniser les pratiques de capture (résolution minimale 20 Mpx, polarisation croisée, champ 10×) et les grilles d'annotation entre les six centres du réseau, avec un coefficient de variation inter-opérateur inférieur à 12 % sur les scores ABCDE.

**Objectif 5 — Intégration clinique responsable.** Déployer le module IA en mode « copilote » : le dermatologue conserve la décision finale ; le système fournit un score, une cartographie des zones d'attention (Grad-CAM) et une synthèse des critères ABCDE déclenchés.

Ces objectifs seront évalués trimestriellement par un comité scientifique mixte (cliniciens, data scientists, représentants patients).

---

## 4. Apports scientifiques attendus

Le projet DermaScan-AI ambitionne plusieurs contributions à l'état de l'art en dermatologie numérique et en intelligence artificielle médicale.

**Protocole de validation clinique prospective.** Mise en place d'une étude multicentrique ouverte sur 24 mois, incluant au minimum 4 500 lésions annotées par double lecture expert. Le protocole prévoit une séparation stricte entraînement / validation / test, avec verrouillage des jeux avant toute analyse de performance.

**Corpus d'images dermoscopiques enrichi.** Constitution d'une base de données structurée comprenant métadonnées cliniques (localisation, phototype, antécédents), scores ABCDE, diagnostics histologiques de référence et masques d'annotation pour les régions d'intérêt. Le corpus simulé pour l'atelier compte plus de 12 000 images réparties sur les six centres.

**Publications visées.** Trois axes de publication sont identifiés : (a) performance diagnostique du modèle sur cohorte externe ; (b) analyse d'équité entre phototypes et tranches d'âge ; (c) acceptabilité et confiance des praticiens face au copilote IA (enquête qualitative n = 80).

**Explainability et gouvernance.** Intégration de cartes d'activation (Grad-CAM) et de rapports structurés listant les critères ABCDE activés par le modèle. Les apports en matière de transparence algorithmique visent à répondre aux exigences du règlement européen sur l'IA (AI Act) pour les systèmes à haut risque en santé.

**Transfert et réplicabilité.** Publication d'un pipeline open source (prétraitement, entraînement, évaluation) et d'un sous-ensemble anonymisé du corpus pour permettre la comparaison avec d'autres approches (Vision Transformers, modèles multimodaux texte-image).

---

## 5. Réseau de centres DermaScan

Le réseau comprend six centres opérationnels en 2024, chacun disposant d'un plateau d'imagerie dermoscopique et d'un accès à la plateforme DermaScan-Cloud :

| Centre | Ville / zone | Médecins | Consultations annuelles (2024 simulé) |
|--------|--------------|----------|---------------------------------------|
| Bastille | Paris 11e | 5 | 1 380 |
| Paris Nord | Saint-Denis / Plaine | 6 | 1 720 |
| Paris Sud | Massy / Orsay | 6 | 1 590 |
| Bordeaux | Métropole bordelaise | 4 | 980 |
| Lille | Métropole lilloise | 4 | 1 050 |
| Marseille | Aix-Marseille | 5 | 1 210 |

Les indicateurs agrégés du réseau (données simulées pour l'atelier) : 53 800 patients suivis, 7 930 consultations de dépistage, 136 mélanomes détectés et confirmés, 33 dermatologues et infirmières imagerie en activité.

Chaque centre applique le même référentiel de bonnes pratiques (RBP-DermaScan v2.3) et participe à une revue de morbidité mensuelle par visioconférence.

---

## 6. Protocole de dépistage

Le parcours patient standardisé DermaScan comprend quatre étapes séquentielles, d'une durée totale de 45 à 60 minutes.

**Étape A — Accueil et anamnèse structurée.** Collecte des antécédents (mélanome familial, épisodes de coups de soleil sévères, immunosuppression), du phototype Fitzpatrick, de la liste des médicaments photosensibilisants et du nombre de naevus auto-déclarés.

**Étape B — Examen clinique complet.** Inspection visuelle de l'ensemble du tégument, incluant cuir chevelu, interdigitales, ongles et muqueuses accessibles. Les lésions suspectes sont repérées selon la règle ABCDE (Asymétrie, Bords irréguliers, Couleur hétérogène, Diamètre > 6 mm, Evolution).

**Étape C — Cartographie corporelle numérique.** Capture de 24 vues standardisées (face, dos, profils, membres) à l'aide d'un cabine d'imagerie totale. Les images servent de référence pour le suivi comparatif à 12 mois.

**Étape D — Dermoscopie ciblée.** Pour chaque lésion classée « à surveiller » ou « suspecte », acquisition d'au moins deux images dermoscopiques : une en lumière polarisée non croisée, une en polarisation croisée. Le dermatologue documente les structures dermoscopiques observées (réseau pigmentaire, globules, voiles blancs, structures vasculaires atypiques).

La dermoscopie constitue le cœur du flux DermaScan-AI : les images de l'étape D alimentent directement le module de classification. Les critères d'inclusion pour l'analyse automatique sont : résolution ≥ 20 Mpx, netteté suffisante (score Laplacien > seuil calibré), et consentement patient pour le traitement algorithmique.

En cas de score d'alerte élevé, le patient est orienté sous 15 jours vers une exérèse-diagnostic ou une confocaliste selon la localisation anatomique.

---

## 7. Pipeline IA DermaScan-AI

L'architecture technique du module IA repose sur un pipeline en cinq blocs, déployé en conteneurs sur l'infrastructure DermaScan-Cloud (région UE).

**Ingestion et contrôle qualité.** Vérification automatique du format DICOM ou JPEG, extraction des métadonnées EXIF, détection de flou et rejet des captures non conformes avec notification au praticien.

**Prétraitement.** Normalisation des couleurs (correction illuminant D65), recadrage centré sur la lésion, augmentation contrôlée à l'entraînement (rotation ± 15°, variation luminosité ± 10 %).

**Modèle de classification.** Backbone EfficientNet-B4 fine-tuné, tête de classification multi-classe (mélanome, naevus bénin, kératose séborrhéique, carcinome basocellulaire, autre). Sortie : probabilités calibrées (temperature scaling) et score d'alerte agrégé sur échelle 0–100.

**Module explainability.** Génération de cartes Grad-CAM superposées à l'image source ; extraction des critères ABCDE correspondant aux zones activées (heuristique rule-based couplée au classifieur).

**Interface clinique.** Tableau de bord web affichant la galerie d'images, le score, la synthèse ABCDE et l'historique des décisions. Le dermatologue valide, modifie ou rejette la proposition IA ; chaque action est journalisée pour audit.

Les performances cibles sur le jeu de test verrouillé (simulation atelier) : AUC-ROC 0,94 pour le mélanome vs. bénin, F1-score 0,89 sur la classe mélanome, temps d'inférence médian 180 ms par image sur GPU T4.

---

## 8. Gouvernance des données et conformité

Le traitement des données de santé au sein de DermaScan-AI respecte le cadre RGPD et les recommandations de la CNIL pour les systèmes d'aide à la décision médicale.

**Base légale.** Intérêt public en matière de santé (article 9.2.i RGPD) et consentement éclairé spécifique pour l'utilisation des images à des fins de recherche algorithmique.

**Anonymisation.** Pseudonymisation systématique des identifiants patients ; séparation physique entre table d'identité (HSM) et corpus d'images ; suppression des métadonnées EXIF contenant des identifiants avant indexation.

**Durée de conservation.** Images brutes : 20 ans (obligation légale dossier patient). Jeu de recherche anonymisé : 10 ans renouvelables par le comité d'éthique.

**Comité d'éthique.** Avis favorable simulé du CPP Île-de-France XI sous le numéro de dossier fictif 2024-AI-DS-042.

**Sécurité.** Chiffrement AES-256 au repos, TLS 1.3 en transit, authentification MFA pour les praticiens, journaux d'accès conservés 3 ans.

Aucune donnée réelle de patient n'est incluse dans le présent document ni dans les jeux de démonstration de l'atelier RAG.

---

## 9. Indicateurs clés 2024 (données simulées)

Synthèse consolidée du réseau pour l'exercice 2024 (fictif) :

- Chiffre d'affaires consolidé : 2,94 M€
- Patients uniques suivis : 53 800
- Consultations de dépistage : 7 930
- Mélanomes détectés et confirmés : 136
- Taux de conversion consultation → biopsie : 18,4 %
- Délai médian consultation → résultat histologique : 11 jours
- Satisfaction patient (NPS) : +62

Répartition par centre (extrait) :

- Bastille : 9 200 patients, 1 380 consultations, 24 mélanomes
- Paris Nord : 11 500 patients, 1 720 consultations, 31 mélanomes
- Paris Sud : 10 800 patients, 1 590 consultations, 28 mélanomes
- Bordeaux : 6 800 patients, 980 consultations, 15 mélanomes
- Lille : 7 400 patients, 1 050 consultations, 18 mélanomes
- Marseille : 8 100 patients, 1 210 consultations, 20 mélanomes

Ces chiffres sont cohérents avec le fichier example.csv utilisé pour la branche SQL de l'application atelier.

---

## 10. Feuille de route R&D 2025–2027

**2025 — Consolidation.** Finalisation du protocole multicentrique, gel du jeu de test, première publication sur la performance diagnostique, déploiement du copilote IA en mode shadow (recommandations non visibles patient).

**2026 — Déploiement actif.** Activation du copilote en production dans les six centres, formation des 33 praticiens, audit d'équité inter-phototypes, enquête acceptabilité.

**2027 — Extension.** Évaluation d'un modèle multimodal (image + texte libre de l'anamnèse), étude de faisabilité télé-dermoscopie, préparation dossier marquage CE selon AI Act.

Le comité de pilotage DermaScan-AI se réunit trimestriellement. Les livrables incluent rapports d'audit, mises à jour du modèle (versioning sémantique) et documentation utilisateur pour les dermatologues.

---

## Glossaire

- **ABCDE** : règle clinique d'alerte sur les mélanomes (Asymétrie, Bords, Couleur, Diamètre, Evolution).
- **Dermoscopie** : examen non invasif de lésions cutanées à l'aide d'un dermatoscope (grossissement 10×).
- **Grad-CAM** : technique d'interprétation visualisant les zones de l'image influençant la décision du modèle.
- **RAG** : Retrieval-Augmented Generation — génération de réponses enrichies par recherche documentaire.

---

*Fin du document — DermaScan fiche projet démonstration RAG v1.0*
