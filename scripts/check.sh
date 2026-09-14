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
echo "==> Checking Python files..."
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest -q

echo
echo "==> Checking spelling..."
uv run typos

echo
echo "==> Checking shell scripts..."
find . \
    \( -path './.git' -o -path './.venv' \) -prune -o \
    -type f -name '*.sh' \
    -exec uv run shellcheck --severity=warning {} +

# Check Zsh scripts and startup files with their own parser.
if command -v zsh >/dev/null 2>&1; then
    while IFS= read -r -d '' script; do
        case "$script" in
            *.sh)
                IFS= read -r shebang < "$script"
                [[ "$shebang" == '#!'*zsh* ]] || continue
                ;;
        esac
        zsh -f -n "$script"
    done < <(find . \
        \( -path './.git' -o -path './.venv' \) -prune -o \
        -type f \( -name '*.sh' -o -name '*.zsh' -o -name '.zshrc*' \
            -o -name '.zshenv*' -o -name '.zimrc' \) -print0)
else
    printf "\033[33mSkipping zsh syntax checks because zsh is not installed.\033[0m\n"
fi

# Check PowerShell scripts and modules with their own parser.
if powershell=$(command -v pwsh || command -v pwsh-preview); then
    find . \
        \( -path './.git' -o -path './.venv' \) -prune -o \
        -type f \( -name '*.ps1' -o -name '*.psm1' \) \
        -exec "$powershell" -NoProfile -File ./scripts/check-pwsh.ps1 {} +
else
    printf "\033[33mSkipping pwsh syntax checks because pwsh is not installed.\033[0m\n"
fi

echo
printf '\033[32m==> All checks passed!\033[0m\n'
