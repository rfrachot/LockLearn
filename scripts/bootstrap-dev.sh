#!/usr/bin/env bash
set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt

if command -v npm >/dev/null 2>&1; then
  (cd frontend && npm install)
else
  echo "npm not found: frontend dependencies were not installed" >&2
fi

python datasets/tools/validate_resources.py

echo
echo "Bootstrap complete. Activate with: source .venv/bin/activate"
echo "Before P0 coding, record the VM's Python/Node/HA versions in PROJECT.md."
