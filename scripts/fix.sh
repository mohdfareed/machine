#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."

echo "==> Syncing dependencies..."
uv sync --dev

echo "==> Fixing script permissions..."
find . \
    \( -path './.git' -o -path './.venv' \) -prune -o \
    -type f \( -path '*/scripts/*.sh' -o -path '*/scripts/*.py' \) \
    -exec chmod +x {} +

echo
echo "==> Formatting and auto-fixing..."
uv run ruff format .
uv run ruff check --fix .

echo
"$(dirname "$0")/check.sh"
