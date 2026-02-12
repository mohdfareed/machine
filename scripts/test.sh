#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

echo "==> Updating dependencies..."
uv lock --upgrade
uv sync --dev

echo
echo "==> Formatting..."
uv run ruff format

echo
echo "==> Linting..."
uv run ruff check --fix

echo
echo "==> Type checking..."
uv run pyright

echo
echo "==> Checking docs generation..."
./scripts/docs.sh

echo
echo "==> All checks passed!"
