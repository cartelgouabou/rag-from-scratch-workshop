#!/usr/bin/env bash
# Setup Mac idempotent : Homebrew, Python 3.11, VS Code, Docker Desktop, venv atelier.
# À lancer depuis la racine du projet (clone git ou ZIP décompressé).
set -euo pipefail

VENV_NAME=".venv-notebook"
REQUIREMENTS="notebooks/requirements-notebook.txt"
KERNEL_NAME="rag-workshop"
KERNEL_DISPLAY="RAG Workshop"
VSCODE_EXT_PYTHON="ms-python.python"
VSCODE_EXT_JUPYTER="ms-toolsai.jupyter"
DOCKER_WAIT_SECONDS=120

SKIP_DOCKER=false
SKIP_PIP=false

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}"

log() { printf '\n\033[1;32m==>\033[0m %s\n' "$*"; }
warn() { printf '\n\033[1;33m!!>\033[0m %s\n' "$*" >&2; }
die() { printf '\n\033[1;31mERR>\033[0m %s\n' "$*" >&2; exit 1; }

have_cmd() { command -v "$1" >/dev/null 2>&1; }

usage() {
  cat <<'EOF'
Usage: ./setup-mac.sh [options]

Installe uniquement ce qui manque (Mac + Homebrew) :
  - python@3.11, Visual Studio Code, Docker Desktop (cask)
  - .venv-notebook + pip install requirements-notebook.txt
  - kernel Jupyter « RAG Workshop », fichier .env

Prérequis : lancer depuis la racine du projet (compose.yaml présent).
            Xcode CLT installés (xcode-select --install).

Options:
  --skip-docker   Ne pas installer / démarrer Docker Desktop
  --skip-pip      Ne pas installer les dépendances pip (venv créé quand même)
  -h, --help      Afficher cette aide
EOF
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --skip-docker) SKIP_DOCKER=true ;;
      --skip-pip) SKIP_PIP=true ;;
      -h | --help)
        usage
        exit 0
        ;;
      *)
        die "Option inconnue : $1 (voir --help)"
        ;;
    esac
    shift
  done
}

assert_repo_root() {
  cd "${PROJECT_ROOT}"
  if [[ ! -f compose.yaml ]] || [[ ! -f "${REQUIREMENTS}" ]]; then
    die "Lancez ce script depuis la racine du projet (dossier avec compose.yaml et ${REQUIREMENTS})."
  fi
  log "Racine projet : ${PROJECT_ROOT}"
}

ensure_clt() {
  if xcode-select -p >/dev/null 2>&1; then
    log "Xcode CLT : déjà installés"
    return 0
  fi
  die "Xcode Command Line Tools manquants.
Exécutez dans un autre terminal :
  xcode-select --install
Puis relancez : ./setup-mac.sh"
}

ensure_brew_shellenv() {
  if have_cmd brew; then
    return 0
  fi
  if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [[ -x /usr/local/bin/brew ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
}

ensure_brew() {
  ensure_brew_shellenv
  if have_cmd brew; then
    log "Homebrew : déjà installé ($(brew --version | head -1))"
    return 0
  fi
  log "Homebrew : installation (mot de passe admin possible)..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  ensure_brew_shellenv
  have_cmd brew || die "Homebrew installé mais 'brew' introuvable. Ajoutez brew au PATH (voir message fin install Homebrew)."
  log "Homebrew : OK"
}

ensure_brew_formula() {
  local formula="$1"
  ensure_brew_shellenv
  if brew list --formula "${formula}" >/dev/null 2>&1; then
    log "brew formula ${formula} : déjà installée"
  else
    log "brew install ${formula}..."
    brew install "${formula}"
  fi
}

ensure_brew_cask() {
  local cask="$1"
  ensure_brew_shellenv
  if brew list --cask "${cask}" >/dev/null 2>&1; then
    log "brew cask ${cask} : déjà installé"
  else
    log "brew install --cask ${cask}..."
    brew install --cask "${cask}"
  fi
}

python311_path() {
  ensure_brew_shellenv
  local prefix
  prefix="$(brew --prefix python@3.11 2>/dev/null)" || die "python@3.11 introuvable. Relancez le script ou : brew install python@3.11"
  echo "${prefix}/bin/python3.11"
}

ensure_docker_running() {
  if [[ "${SKIP_DOCKER}" == true ]]; then
    log "Docker : ignoré (--skip-docker)"
    return 0
  fi

  ensure_brew_cask docker

  if docker info >/dev/null 2>&1; then
    log "Docker : daemon déjà actif"
    return 0
  fi

  log "Docker : démarrage de Docker Desktop (acceptez la licence si première ouverture)..."
  open -a Docker 2>/dev/null || true

  local elapsed=0
  while ! docker info >/dev/null 2>&1; do
    if (( elapsed >= DOCKER_WAIT_SECONDS )); then
      warn "Docker n'a pas répondu en ${DOCKER_WAIT_SECONDS}s."
      warn "Ouvrez Docker Desktop depuis Applications, attendez l'icône verte, puis : docker info"
      return 0
    fi
    sleep 3
    elapsed=$((elapsed + 3))
    printf '.'
  done
  printf '\n'
  log "Docker : daemon actif"
}

ensure_vscode_extensions() {
  if ! have_cmd code; then
    warn "Commande 'code' absente : installez le PATH shell dans VS Code"
    warn "(⇧⌘P → « Shell Command: Install code command in PATH »), puis relancez le script."
    warn "Sinon installez les extensions Python et Jupyter manuellement."
    return 0
  fi
  for ext in "${VSCODE_EXT_PYTHON}" "${VSCODE_EXT_JUPYTER}"; do
    log "Extension VS Code : ${ext}"
    code --install-extension "${ext}" --force 2>/dev/null || code --install-extension "${ext}"
  done
}

ensure_venv() {
  local py311 venv_python
  py311="$(python311_path)"
  if [[ ! -x "${py311}" ]]; then
    die "Interpréteur introuvable : ${py311}"
  fi

  if [[ -x "${PROJECT_ROOT}/${VENV_NAME}/bin/python" ]]; then
    log "venv ${VENV_NAME} : déjà présent"
  else
    log "Création du venv ${VENV_NAME} avec ${py311}..."
    "${py311}" -m venv "${PROJECT_ROOT}/${VENV_NAME}"
  fi

  venv_python="${PROJECT_ROOT}/${VENV_NAME}/bin/python"
  [[ -x "${venv_python}" ]] || die "venv invalide : ${venv_python}"
  echo "${venv_python}"
}

ensure_pip_deps() {
  if [[ "${SKIP_PIP}" == true ]]; then
    log "pip : ignoré (--skip-pip)"
    return 0
  fi

  local venv_python="$1"
  local venv_pip="${PROJECT_ROOT}/${VENV_NAME}/bin/pip"

  log "Mise à jour de pip (peut prendre 10–20 min avec PyTorch)..."
  "${venv_python}" -m pip install --upgrade pip
  log "Installation : ${REQUIREMENTS}"
  "${venv_pip}" install -r "${PROJECT_ROOT}/${REQUIREMENTS}"
}

ensure_ipykernel() {
  if [[ "${SKIP_PIP}" == true ]]; then
    return 0
  fi

  local venv_python="${PROJECT_ROOT}/${VENV_NAME}/bin/python"
  log "Kernel Jupyter : ${KERNEL_DISPLAY}"
  "${venv_python}" -m ipykernel install --user --name "${KERNEL_NAME}" --display-name "${KERNEL_DISPLAY}"
}

ensure_env_file() {
  if [[ -f "${PROJECT_ROOT}/.env" ]]; then
    log ".env : déjà présent (non modifié)"
  else
    cp "${PROJECT_ROOT}/.env.example" "${PROJECT_ROOT}/.env"
    log ".env : créé depuis .env.example — renseignez VERCEL_AI_GATEWAY_KEY pour le notebook §7"
  fi
}

print_summary() {
  cat <<EOF

================================================================================
Setup terminé — ${PROJECT_ROOT}
================================================================================

Notebook atelier :
  1. Ouvrir VS Code → File → Open Folder → ce dossier
  2. Ouvrir notebooks/rag_atelier_presentation.ipynb
  3. Kernel : « ${KERNEL_DISPLAY} » ou ${VENV_NAME}/bin/python

Configurer (section 7 du notebook) :
  Éditez .env → VERCEL_AI_GATEWAY_KEY=...

Application Docker (optionnel, manuel) :
  docker compose up --build
  → http://localhost:3001

Réactiver le venv plus tard :
  source ${VENV_NAME}/bin/activate

EOF
}

main() {
  parse_args "$@"
  assert_repo_root
  ensure_clt
  ensure_brew
  ensure_brew_formula python@3.11
  ensure_brew_cask visual-studio-code
  ensure_vscode_extensions
  ensure_docker_running

  local venv_python
  venv_python="$(ensure_venv)"
  ensure_pip_deps "${venv_python}"
  ensure_ipykernel
  ensure_env_file
  print_summary
}

main "$@"
