#!/usr/bin/env bash
set -euo pipefail

echo "updating pre-commit hooks..."
# FIXME: black and isort dropped support for Python 3.8
# if [ -f .venv/bin/pre-commit ]; then
#   "./.venv/bin/pre-commit" autoupdate || true
# else
#   pre-commit autoupdate || true
# fi
