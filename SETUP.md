# Installation Mac — atelier notebook (Homebrew)

Guide pour exécuter [`notebooks/rag_atelier_presentation.ipynb`](notebooks/rag_atelier_presentation.ipynb) dans **VS Code**. Le **setup automatisé** prend en général 15–25 min (surtout `pip` / PyTorch).

## Ce que vous installez

| Composant | Rôle |
|-----------|------|
| Archive ZIP | Code du projet depuis GitHub |
| Script [`setup-mac.sh`](setup-mac.sh) (racine) | Installe uniquement ce qui manque (recommandé) |
| Xcode CLT | Compilateur Apple ; requis par Homebrew |
| Homebrew | Python 3.11, VS Code, Docker Desktop |
| `.venv-notebook` | Environnement Python du notebook |
| `requirements-notebook.txt` | Libs pip (autonome, sans `backend/requirements.txt`) |

La **section 7** du notebook nécessite `VERCEL_AI_GATEWAY_KEY` dans `.env`. Les étapes 1–6 fonctionnent sans clé.

**Limites du script** (actions manuelles possibles) : installation des CLT (`xcode-select --install`), mot de passe admin Homebrew, licence Docker Desktop au premier lancement, commande shell `code` dans VS Code.

---

## 1. Récupérer le projet

**Option A — Git (recommandé pour tester le script à la racine)**

```bash
git clone https://github.com/cartelgouabou/rag-from-scratch-workshop.git
cd rag-from-scratch-workshop
```

**Option B — ZIP** : [cartelgouabou/rag-from-scratch-workshop](https://github.com/cartelgouabou/rag-from-scratch-workshop) → **Code** → **Download ZIP**, puis :

```bash
cd ~/Downloads
unzip rag-from-scratch-workshop-main.zip
cd rag-from-scratch-workshop-main
```

Vérifiez la présence de `setup-mac.sh`, `backend/`, `notebooks/`, `compose.yaml`, `.env.example`.

---

## 2. Setup rapide (script)

**Prérequis** : Xcode CLT installés une fois (`xcode-select --install` si le script le demande).

Depuis la **racine du projet** :

```bash
chmod +x setup-mac.sh   # une fois si besoin
./setup-mac.sh
```

Le script vérifie chaque outil **avant** de l’installer :

- Homebrew (si absent)
- `python@3.11`, VS Code, Docker Desktop (casks/formulas manquants seulement)
- Extensions VS Code Python + Jupyter (si `code` est dans le PATH)
- `.venv-notebook`, `pip install -r notebooks/requirements-notebook.txt`
- Kernel **RAG Workshop**, fichier `.env` (sans écraser un `.env` existant)

Options :

```bash
./setup-mac.sh --skip-docker   # atelier notebook sans Docker Desktop
./setup-mac.sh --skip-pip      # outils brew/venv seulement
./setup-mac.sh --help
```

Puis [**§ 3 — Lancer l’atelier dans VS Code**](#3--lancer-latelier-dans-vs-code).

---

## 3. Lancer l’atelier dans VS Code

1. **File → Open Folder** → dossier du projet (`rag-from-scratch-workshop-main`).
2. Ouvrir [`notebooks/rag_atelier_presentation.ipynb`](notebooks/rag_atelier_presentation.ipynb).
3. **Select Kernel** → **RAG Workshop** ou `./.venv-notebook/bin/python`.
4. PDF démo dans [`data/samples/`](data/samples/) si besoin.
5. Exécuter les cellules dans l’ordre.

Éditez `.env` : `VERCEL_AI_GATEWAY_KEY` pour la section 7.

**Application complète (Docker, optionnel)** — après installation de Docker Desktop par le script :

```bash
docker compose up --build
```

→ [http://localhost:3001](http://localhost:3001)

---

## Détail manuel (si le script échoue)

### A. Outils Apple

```bash
xcode-select --install
```

### B. Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
eval "$(/opt/homebrew/bin/brew shellenv)"   # Apple Silicon, si besoin
```

### C. Python 3.11 et VS Code

```bash
brew install python@3.11
brew install --cask visual-studio-code
```

### D. Extensions VS Code

⇧⌘P → **Shell Command: Install 'code' command in PATH**, puis :

```bash
code --install-extension ms-python.python
code --install-extension ms-toolsai.jupyter
```

### E. Docker Desktop (optionnel)

```bash
brew install --cask docker
open -a Docker
```

### F. venv et dépendances

```bash
python3.11 -m venv .venv-notebook
source .venv-notebook/bin/activate
python -m pip install --upgrade pip
pip install -r notebooks/requirements-notebook.txt
python -m ipykernel install --user --name rag-workshop --display-name "RAG Workshop"
cp -n .env.example .env
```

---

## Dépannage

| Problème | Action |
|----------|--------|
| Script : « racine projet » | `cd` dans le dossier décompressé (voir §1) |
| CLT manquants | `xcode-select --install`, relancer le script |
| `command not found: brew` | `eval "$(/opt/homebrew/bin/brew shellenv)"` |
| `command not found: python3.11` | `brew install python@3.11` |
| Extensions VS Code | Installer `code` dans le PATH (§D) |
| Mauvais kernel | **Python: Select Interpreter** → `./.venv-notebook/bin/python` |
| Docker ne démarre pas | Ouvrir Docker Desktop, accepter la licence, `docker info` |
| Erreur 429 Gateway (§7) | Pause entre les deux cellules de génération |
| OCR DocTR lent | Éviter les PDF scannés en démo live |

---

## Rappel formateur

- Distribuer le [ZIP](https://github.com/cartelgouabou/rag-from-scratch-workshop/archive/refs/heads/main.zip) **avant** l’atelier.
- Les participants : décompresser (ou `git clone`) → `cd` → `./setup-mac.sh`.
- Venv : **`.venv-notebook`** ; Python : **`python3.11`** ; pip : **`notebooks/requirements-notebook.txt`** seul.
