#!/bin/bash
#
# run_app.command — Instalador + launcher (macOS) · Apuração · Agita
# Otimizado para MacBook Air M2, 8 GB de RAM unificada.
#
# Dê dois cliques no Finder. Na 1ª vez instala tudo (Python deps, Ollama,
# modelo); nas próximas só abre a aplicação. É seguro rodar várias vezes.
#
set -uo pipefail

cd "$(dirname "$0")"
ROOT="$(pwd)"
VENV="$ROOT/.venv"
MODEL="qwen2.5:3b-instruct-q5_K_M"   # deve bater com config/analysis/semantic.toml

bold() { printf "\n\033[1m%s\033[0m\n" "$1"; }
ok()   { printf "  \033[32m\xE2\x9C\x93\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }
die()  { printf "  \033[31m\xE2\x9C\x97 %s\033[0m\n" "$1"; echo; read -r -p "Pressione Enter para fechar..." _; exit 1; }

bold "Apuração · Agita — instalação e inicialização"

# ── 1) Python 3.11+ (o projeto usa tomllib, que exige 3.11) ──────────────────
PY=""
for c in python3.13 python3.12 python3.11 python3; do
  if command -v "$c" >/dev/null 2>&1; then
    if "$c" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)' 2>/dev/null; then
      PY="$c"; break
    fi
  fi
done
if [ -z "$PY" ]; then
  warn "Python 3.11+ não encontrado."
  if command -v brew >/dev/null 2>&1; then
    echo "  Instalando Python via Homebrew..."
    brew install python@3.12 || die "Falha ao instalar o Python."
    PY=python3.12
  else
    die "Instale o Python 3.11+ (https://www.python.org/downloads/macos/) e rode de novo."
  fi
fi
ok "Python: $($PY --version 2>&1)"

# ── 2) Ambiente virtual + dependências Python ────────────────────────────────
if [ ! -d "$VENV" ]; then
  echo "  Criando ambiente virtual (.venv)..."
  "$PY" -m venv "$VENV" || die "Falha ao criar o ambiente virtual."
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"

STAMP="$VENV/.deps-installed"
if [ ! -f "$STAMP" ] || [ requirements.txt -nt "$STAMP" ]; then
  echo "  Instalando dependências Python (demora alguns minutos na 1ª vez)..."
  python -m pip install --upgrade pip >/dev/null
  python -m pip install -r requirements.txt || die "Falha ao instalar as dependências."
  touch "$STAMP"
  ok "Dependências instaladas."
else
  ok "Dependências já instaladas."
fi

# ── 3) Ollama (LLM local) ────────────────────────────────────────────────────
if ! command -v ollama >/dev/null 2>&1; then
  warn "Ollama não encontrado."
  if command -v brew >/dev/null 2>&1; then
    echo "  Instalando Ollama via Homebrew..."
    brew install ollama || die "Falha ao instalar o Ollama."
  else
    die "Instale o Ollama em https://ollama.com/download e rode de novo."
  fi
fi
ok "Ollama: $(ollama --version 2>&1 | head -1)"

# Otimizações de memória/velocidade para Apple Silicon com 8 GB
export OLLAMA_FLASH_ATTENTION=1     # atenção eficiente em memória (menor KV cache)
export OLLAMA_MAX_LOADED_MODELS=1   # nunca manter mais de 1 modelo na RAM
export PYTORCH_ENABLE_MPS_FALLBACK=1
export TOKENIZERS_PARALLELISM=false

# Garante o serviço do Ollama no ar (se já roda via app desktop, reaproveita)
if ! curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "  Iniciando serviço do Ollama..."
  ollama serve >/dev/null 2>&1 &
  for _ in $(seq 1 30); do
    curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1 && break
    sleep 1
  done
fi

# Baixa o modelo só se ainda não estiver presente
if ! ollama list 2>/dev/null | grep -q "$MODEL"; then
  echo "  Baixando modelo $MODEL (~2,3 GB, só na 1ª vez)..."
  ollama pull "$MODEL" || die "Falha ao baixar o modelo."
fi
ok "Modelo pronto: $MODEL"

# ── 4) Sobe a aplicação (server.py abre o navegador sozinho em :8501) ─────────
bold "Abrindo a aplicação em http://127.0.0.1:8501 ..."
python server.py
