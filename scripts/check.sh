#!/usr/bin/env zsh
set -Eeuo pipefail

cd "$(dirname "$0")/.."
echo "==> Checking dependency updates..."
# ═════════════════════════════════════════════════════════════════════════════

uv lock --check
uv lock --upgrade --dry-run

# ═════════════════════════════════════════════════════════════════════════════
echo
echo "==> Checking synced dependencies..."
# ═════════════════════════════════════════════════════════════════════════════

uv sync --dev --check

# ═════════════════════════════════════════════════════════════════════════════
echo
echo "==> Checking Python files..."
# ═════════════════════════════════════════════════════════════════════════════

uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest -q

# ═════════════════════════════════════════════════════════════════════════════
echo
echo "==> Checking spelling..."
# ═════════════════════════════════════════════════════════════════════════════

uv run typos

# ═════════════════════════════════════════════════════════════════════════════
echo
echo "==> Checking shell scripts..."
# ═════════════════════════════════════════════════════════════════════════════

find . \
  \( -path './.git' -o -path './.venv' \) -prune -o \
  -type f -name '*.sh' \
  -exec uv run shellcheck --severity=error {} +

# ═════════════════════════════════════════════════════════════════════════════
echo
echo "==> Checking zsh scripts..."
# ═════════════════════════════════════════════════════════════════════════════

# Check Zsh scripts and startup files with their own parser.
while IFS= read -r -d '' script; do
  if [[ "$script" == *.sh ]]; then
    IFS= read -r shebang < "$script" || true
    [[ "$shebang" == '#!'*zsh* ]] || continue
  fi
  zsh -f -n "$script"
done < <(find . \
  \( -path './.git' -o -path './.venv' \) -prune -o \
  -type f \( -name '*.sh' -o -name '*.zsh' -o -name '.zshrc*' \
    -o -name '.zshenv*' -o -name '.zimrc' \) -print0)

# ═════════════════════════════════════════════════════════════════════════════
echo
echo "==> Checking script permissions..."
# ═════════════════════════════════════════════════════════════════════════════

non_executable=$(find . \
  \( -path './.git' -o -path './.venv' \) -prune -o \
  -type f \( -path '*/scripts/*.sh' -o -path '*/scripts/*.py' \) \
  ! -exec test -x {} \; -print -quit)
if [[ -n "$non_executable" ]]; then
  echo "Error: Script is not executable: $non_executable" >&2
  exit 1
fi

# ═════════════════════════════════════════════════════════════════════════════
echo
printf '\033[32m==> All checks passed!\033[0m\n'
