#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$DIR/venv/bin/python"

if [ ! -f "$PYTHON" ]; then
  echo "Virtual environment not found. Run setup first:"
  echo "  python3.11 -m venv venv && venv/bin/pip install kokoro flask soundfile numpy scipy torch"
  exit 1
fi

URL="http://127.0.0.1:5050"

# The torch/numpy wheels are arm64-only. On Apple Silicon under a Rosetta
# (x86_64) shell, Python must be forced to arm64 or the imports crash with
# "incompatible architecture". No-op on real Intel Macs.
ARCHPREFIX=""
if /usr/bin/arch -arm64 /usr/bin/true 2>/dev/null; then
  ARCHPREFIX="/usr/bin/arch -arm64"
fi

echo "Starting Read for Sleep on $URL"
echo "(First run downloads the Kokoro model ~330 MB)"
echo ""

# Open the browser only once the server actually answers, so we never land on a
# blank "can't connect" window.
( for _ in $(seq 1 120); do
    code=$(/usr/bin/curl -s -o /dev/null -w '%{http_code}' "$URL" 2>/dev/null || true)
    [ "$code" = "200" ] && { open "$URL" 2>/dev/null || true; exit 0; }
    sleep 0.5
  done ) &

exec $ARCHPREFIX "$PYTHON" "$DIR/app.py"
