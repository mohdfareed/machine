#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."

echo "==> Checking dependency updates..."
uv lock --check
uv lock --upgrade --dry-run

echo
echo "==> Checking synced dependencies..."
uv sync --dev --check

echo
echo "==> Checking shell scripts..."
find . \
    \( -path './.git' -o -path './.venv' \) -prune -o \
    -type f -name '*.sh' \
    -exec uv run shellcheck --severity=warning {} +

# Check zsh scripts
if command -v zsh >/dev/null 2>&1; then
    while IFS= read -r -d '' script; do
        if grep -q '^#!/usr/bin/env zsh' "$script"; then
            zsh -n "$script"
        fi
    done < <(find . \
        \( -path './.git' -o -path './.venv' \) -prune -o \
        -type f -name '*.sh' -print0)
else
    echo "Skipping zsh syntax checks because zsh is not installed."
fi

echo
echo "==> Checking Python files..."
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run codespell .
uv run pytest -q

echo
printf '\033[32m==> All checks passed!\033[0m\n'
