#!/bin/bash
PROJECT_DIR="/Users/zeynebberenkece/news_digest_agent"
PY="$PROJECT_DIR/venv/bin/python"

OLLAMA_BIN="$(command -v ollama)"
[ -x "$OLLAMA_BIN" ] || OLLAMA_BIN="/opt/homebrew/bin/ollama"
[ -x "$OLLAMA_BIN" ] || OLLAMA_BIN="/usr/local/bin/ollama"

if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "$(date): Ollama kapali, baslatiliyor..."
    "$OLLAMA_BIN" serve >/tmp/ollama.log 2>&1 &
    for i in $(seq 1 30); do
        curl -s http://localhost:11434/api/tags >/dev/null 2>&1 && break
        sleep 1
    done
fi

cd "$PROJECT_DIR" || exit 1
echo "$(date): bulten calistiriliyor"
"$PY" main.py
echo "$(date): bitti"
