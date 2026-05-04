#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$DIR/venv/bin/python"

if [ ! -f "$PYTHON" ]; then
  echo "Virtual environment not found. Run setup first:"
  echo "  python3.11 -m venv venv && venv/bin/pip install kokoro flask soundfile numpy scipy torch"
  exit 1
fi

echo "Starting Read for Sleep on http://127.0.0.1:5050"
echo "(First run downloads the Kokoro model ~330 MB)"
echo ""
open "http://127.0.0.1:5050" 2>/dev/null || true
"$PYTHON" "$DIR/app.py"
