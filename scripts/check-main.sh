#!/usr/bin/env bash
set -euo pipefail

# Non-destructive check to see what's running and bound to the main API port.
# Usage: bash scripts/check-main.sh [PORT]

PORT="${1:-${MAIN_PORT:-8001}}"

echo "==> Checking processes bound to TCP port ${PORT}"
if command -v lsof >/dev/null 2>&1; then
  lsof -Pn -i :"${PORT}" -sTCP:LISTEN || true
elif command -v ss >/dev/null 2>&1; then
  ss -ltnp | awk -v p=":${PORT}" '$4 ~ p' || true
else
  echo "(lsof/ss not available; skipping port listing)"
fi

echo
echo "==> Looking for uvicorn/simple_api processes"
if command -v pgrep >/dev/null 2>&1; then
  pgrep -fal 'uvicorn|simple_api|main:app|simple_api.py' || true
else
  ps aux | egrep 'uvicorn|simple_api|main:app|simple_api.py' | grep -v egrep || true
fi

echo
echo "==> Quick API probe (if a server is listening on ${PORT})"
if command -v curl >/dev/null 2>&1; then
  set +e
  curl -s "http://127.0.0.1:${PORT}/api/internships?q=intern&live=1&limit=5&page=1" | head -c 400; echo
  set -e
else
  echo "(curl not available; skipping probe)"
fi

echo
echo "Hint: If you see uvicorn with 'main:app' and the probe returns JSON with data, you're on the main app."
echo "      If you see 'simple_api.py' or only 12 results, the demo is running."

