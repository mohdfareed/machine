#!/usr/bin/env bash
set -euo pipefail

echo "compiling scripts..."
python -m compileall -qf scripts
python -m compileall -qf bootstrap.py

echo "updating pre-commit hooks..."
if [ -f .venv/bin/pre-commit ]; then
  "./.venv/bin/pre-commit" autoupdate || true
else
  pre-commit autoupdate || true
fi
