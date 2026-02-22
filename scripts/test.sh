#!/usr/bin/env zsh
set -e
cd "$(dirname "$0")/.."

echo "==> Fixing permissions..."
chmod +x ./**/scripts/*.sh
chmod +x ./**/scripts/*.py

echo "==> Updating dependencies..."
uv lock --upgrade
uv sync --dev

echo
echo "==> Running tests..."
uv run ruff format
uv run ruff check --fix
uv run pyright
uv run pytest -q

echo
echo "==> All checks passed!"
