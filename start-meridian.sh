#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

SESSION="meridian"
URL="http://localhost:5173"

if ! command -v poetry >/dev/null 2>&1; then
  echo "error: poetry not found. Install Poetry and run: poetry install" >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "error: npm not found. Install Node.js 18+ and run: cd frontend && npm install" >&2
  exit 1
fi

if [[ ! -d frontend/node_modules ]]; then
  echo "error: frontend dependencies missing. Run: cd frontend && npm install" >&2
  exit 1
fi

start_without_tmux() {
  echo "tmux not found — starting API in background and frontend in this terminal."
  echo
  echo "  Open Meridian: $URL"
  echo
  poetry run python -m meridian.main &
  API_PID=$!
  cleanup() {
    kill "$API_PID" 2>/dev/null || true
  }
  trap cleanup EXIT INT TERM
  cd frontend
  npm run dev
}

if command -v tmux >/dev/null 2>&1; then
  if tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux kill-session -t "$SESSION"
  fi

  tmux new-session -d -s "$SESSION" -c "$ROOT" -n dev \
    "poetry run python -m meridian.main"
  tmux split-window -v -t "$SESSION:dev" -c "$ROOT/frontend" \
    "npm run dev"
  tmux select-layout -t "$SESSION:dev" even-vertical >/dev/null

  echo
  echo "  Meridian is running in tmux session: $SESSION"
  echo "  Open Meridian: $URL"
  echo
  echo "  Detach: Ctrl-b then d"
  echo "  Reattach later: tmux attach -t $SESSION"
  echo

  tmux attach -t "$SESSION"
else
  start_without_tmux
fi
