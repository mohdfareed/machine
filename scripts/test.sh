#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

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
