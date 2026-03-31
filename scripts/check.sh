#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."

echo "==> Syncing dependencies..."
uv sync --dev --locked

echo
echo "==> Running checks..."
shell_scripts="$(mktemp)"
trap 'rm -f "$shell_scripts"' EXIT
find . -name '*.sh' ! -path './.venv/*' -print0 > "$shell_scripts"
if [[ -s "$shell_scripts" ]]; then
    xargs -0 uv run shellcheck --severity=warning < "$shell_scripts"
    while IFS= read -r -d '' f; do
        if head -1 "$f" | grep -q 'env zsh'; then
            zsh -n "$f"
        fi
    done < "$shell_scripts"
fi
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest -q

echo
echo "==> All checks passed!"
