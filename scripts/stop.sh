#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -f .runtime/ollama.pid ]]; then
    echo 'No project-started Ollama to stop. Stop any separately started service manually.'
    exit 0
fi
pid=$(cat .runtime/ollama.pid)
[[ "$pid" =~ ^[0-9]+$ && "$pid" -gt 1 ]] || { echo 'Invalid Ollama PID record.' >&2; exit 1; }

# Check start time too, so an old PID file cannot target a different process.
started=$(cat .runtime/ollama.started)
current=$(ps -p "$pid" -o lstart= || true)
if [[ -n "$started" && "$current" == "$started" ]]; then
    kill "$pid"
    echo 'Sent Ollama a stop signal.'
else
    echo 'Ollama already stopped; removing stale records.'
fi
rm -f .runtime/ollama.pid .runtime/ollama.started
