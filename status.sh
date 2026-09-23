#!/bin/bash
# Show background server status.
ROOT="$(cd "$(dirname "$0")" && pwd)"

check_one() {
  local name="$1" port="$2"
  local pidfile="$ROOT/.pids/${name}.pid"
  if [ -f "$pidfile" ]; then
    local pid
    pid=$(cat "$pidfile")
    if kill -0 "$pid" 2>/dev/null; then
      echo "$name: RUNNING (pid $pid, port $port)"
      return 0
    else
      echo "$name: STOPPED (stale pid $pid)"
      return 1
    fi
  else
    echo "$name: STOPPED (no pid file)"
    return 1
  fi
}

check_one backend 5000
check_one frontend 3000
