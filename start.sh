#!/bin/bash
# Start backend + frontend in the background (survives terminal close via nohup).
# Usage: ./start.sh
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT/.logs" "$ROOT/.pids"

is_running() {
  [ -f "$ROOT/.pids/$1.pid" ] && kill -0 "$(cat "$ROOT/.pids/$1.pid")" 2>/dev/null
}

start_one() {
  local name="$1" dir="$2" port="$3"
  if is_running "$name"; then
    echo "$name already running (pid $(cat "$ROOT/.pids/$name.pid")). Use ./stop.sh first."
    return 0
  fi
  rm -f "$ROOT/.pids/$name.pid"
  [ -d "$ROOT/$dir/venv" ] || { echo "$dir/venv missing. Run setup in README first."; exit 1; }
  echo "Starting $name (port $port) in background..."
  cd "$ROOT/$dir"
  nohup ./venv/bin/python run.py > "$ROOT/.logs/$name.log" 2>&1 &
  echo $! > "$ROOT/.pids/$name.pid"
}

start_one backend backend 5000
start_one frontend frontend 3000

sleep 2
./status.sh 2>/dev/null || true
echo "Logs: .logs/backend.log, .logs/frontend.log"
