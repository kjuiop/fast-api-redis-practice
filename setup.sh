#!/bin/sh

set -eu

VENV_DIR=".venv"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is not installed. Install Python first." >&2
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

"$PYTHON_BIN" -m pip install --upgrade pip
"$PIP_BIN" install fastapi uvicorn redis

echo
echo "Setup complete."
echo "Activate with: source .venv/bin/activate"
echo "Run app later with: .venv/bin/uvicorn app.main:app --reload"