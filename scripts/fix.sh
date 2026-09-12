#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."

echo "==> Upgrading dependencies..."
uv lock --upgrade

echo
echo "==> Syncing dependencies..."
uv sync --dev --locked

echo "==> Fixing script permissions..."
find . \
    \( -path './.git' -o -path './.venv' \) -prune -o \
    -type f \( -path '*/scripts/*.sh' -o -path '*/scripts/*.py' \) \
    -exec chmod +x {} +

echo "==> Formatting and auto-fixing..."
uv run ruff check --fix .
uv run ruff format .
uv run codespell --write-changes .

echo
"$(dirname "$0")/check.sh"
