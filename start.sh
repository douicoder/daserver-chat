#!/bin/bash
# Start backend + frontend in background.
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT/.logs" "$ROOT/.pids"

echo "Starting backend (port 5000)..."
cd "$ROOT/backend"
[ -d venv ] || { echo "backend/venv missing. Run setup in README first."; exit 1; }
nohup ./venv/bin/python run.py > "$ROOT/.logs/backend.log" 2>&1 &
echo $! > "$ROOT/.pids/backend.pid"

echo "Starting frontend (port 3000)..."
cd "$ROOT/frontend"
[ -d venv ] || { echo "frontend/venv missing. Run setup in README first."; exit 1; }
nohup ./venv/bin/python run.py > "$ROOT/.logs/frontend.log" 2>&1 &
echo $! > "$ROOT/.pids/frontend.pid"

sleep 2
echo "Backend:  http://localhost:5000 (log: .logs/backend.log)"
echo "Frontend: http://localhost:3000 (log: .logs/frontend.log)"
