#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# .env is local shell configuration; only source a file you trust.
if [[ -f .env ]]; then
    set -a
    source .env
    set +a
fi
export OLLAMA_HOST="${OLLAMA_HOST:-http://127.0.0.1:11434}"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$PWD/.uv-cache}"
uv sync --locked

ready() { curl --fail --silent --max-time 2 "$OLLAMA_HOST/api/version" >/dev/null; }
if ! ready; then
    case "$OLLAMA_HOST" in
        http://localhost:*|http://127.0.0.1:*) ;;
        *) echo 'Start the configured Ollama server manually.' >&2; exit 1 ;;
    esac
    mkdir -p .runtime
    nohup ollama serve >.runtime/ollama.log 2>&1 </dev/null &
    pid=$!
    echo "$pid" >.runtime/ollama.pid
    ps -p "$pid" -o lstart= >.runtime/ollama.started
    for ((attempt=0; attempt<30; attempt++)); do
        ready && break
        sleep 1
    done
    ready || { echo 'Ollama did not start. Check .runtime/ollama.log, then run scripts/stop.sh.' >&2; exit 1; }
fi

# Ollama stays running until you call stop.sh (or stop it manually).
if [[ "${1:-}" == '--check' ]]; then
    exec uv run --locked python llm.py 'Say hello in one sentence.'
fi
exec uv run --locked python main.py
