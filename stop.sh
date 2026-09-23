#!/bin/bash
# Stop backend + frontend started by start.sh.
ROOT="$(cd "$(dirname "$0")" && pwd)"

stop_pid() {
  local name="$1"
  local pidfile="$ROOT/.pids/${name}.pid"
  if [ -f "$pidfile" ]; then
    local pid
    pid=$(cat "$pidfile")
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" && echo "Stopped $name (pid $pid)"
    else
      echo "$name already stopped (stale pid $pid)"
    fi
    rm -f "$pidfile"
  else
    echo "No pid file for $name"
  fi
}

stop_pid backend
stop_pid frontend

# Fallback: kill leftovers by pattern (only this repo's run.py)
pkill -f "daserver-chat/backend/run.py" 2>/dev/null && echo "Killed leftover backend" || true
pkill -f "daserver-chat/frontend/run.py" 2>/dev/null && echo "Killed leftover frontend" || true

echo "Done."
