#!/usr/bin/env zsh
# shellcheck shell=bash
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
# shellcheck disable=SC2207
all_scripts=($(find . -name '*.sh' ! -path './.venv/*'))
uv run shellcheck --severity=warning "${all_scripts[@]}"
for f in "${all_scripts[@]}"; do
    head -1 "$f" | grep -q 'env zsh' && zsh -n "$f"
done
uv run ruff format
uv run ruff check --fix
uv run pyright
uv run pytest -q

echo
echo "==> All checks passed!"
