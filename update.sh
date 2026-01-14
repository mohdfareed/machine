#!/usr/bin/env bash
set -euo pipefail

echo "compiling scripts..."
python -m compileall -qf machine
python -m compileall -qf setup.py

# Legacy (remove when chezmoi/ is deleted)
if [ -d scripts ]; then
  python -m compileall -qf scripts
fi
if [ -f bootstrap.py ]; then
  python -m compileall -qf bootstrap.py
fi

echo "updating pre-commit hooks..."
if [ -f .venv/bin/pre-commit ]; then
  "./.venv/bin/pre-commit" autoupdate || true
else
  pre-commit autoupdate || true
fi
