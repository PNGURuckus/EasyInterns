#!/usr/bin/env bash
set -euo pipefail

# Ensure the main FastAPI app (main:app) is the only server running.
# - Kills demo/simple servers
# - Frees the target port
# - Starts uvicorn main:app

MAIN_PORT="${MAIN_PORT:-8001}"

echo "[1/4] Checking for processes bound to port ${MAIN_PORT}..."
PIDS=$(lsof -t -i :"${MAIN_PORT}" -sTCP:LISTEN 2>/dev/null || true)
if [[ -n "${PIDS}" ]]; then
  echo "    Killing: ${PIDS}"
  kill ${PIDS} || true
  sleep 1
fi

echo "[2/4] Killing known demo servers (if any)..."
pkill -f "simple_api.py" 2>/dev/null || true
pkill -f "uvicorn .*simple_api" 2>/dev/null || true
pkill -f "uvicorn .*backend.main" 2>/dev/null || true

echo "[3/4] Verifying port is free..."
if lsof -i :"${MAIN_PORT}" -sTCP:LISTEN -P -n 1>/dev/null 2>&1; then
  echo "    ERROR: Port ${MAIN_PORT} is still in use. Exiting." >&2
  exit 1
fi

echo "[4/4] Starting main app on :${MAIN_PORT}..."
exec uvicorn main:app --reload --port "${MAIN_PORT}" --log-level info

