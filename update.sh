#!/usr/bin/env bash
set -euo pipefail

echo "compiling scripts..."
python -m compileall -qf chezmoi
python -m compileall -qf config
python -m compileall -qf machines
python -m compileall -qf scripts
python -m compileall -qf bootstrap.py

echo "updating pre-commit hooks..."
# FIXME: black and isort dropped support for Python 3.8
# if [ -f .venv/bin/pre-commit ]; then
#   "./.venv/bin/pre-commit" autoupdate || true
# else
#   pre-commit autoupdate || true
# fi
