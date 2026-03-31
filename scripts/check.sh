#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."

echo "==> Syncing dependencies..."
uv sync --dev --locked

echo
echo "==> Running checks..."

shell_scripts="$(mktemp)"
python_scripts="$(mktemp)"
trap 'rm -f "$shell_scripts" "$python_scripts"' EXIT

find . -name '*.sh' ! -path './.venv/*' -print0 > "$shell_scripts"
if [[ -s "$shell_scripts" ]]; then
    xargs -0 uv run shellcheck --severity=warning < "$shell_scripts"
    while IFS= read -r -d '' f; do
        if head -1 "$f" | grep -q 'env zsh'; then
            zsh -n "$f"
        fi
    done < "$shell_scripts"
fi

find . -name '*.py' ! -path './.venv/*' -print0 > "$python_scripts"
if [[ -s "$python_scripts" ]]; then
    xargs -0 uv run python -c \
        'import pathlib, sys; [compile(pathlib.Path(path).read_text(encoding="utf-8"), path, "exec") for path in sys.argv[1:]]' \
        < "$python_scripts"
fi

uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest -q

echo
echo "==> All checks passed!"
