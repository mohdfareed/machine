#!/usr/bin/env sh
set -eu

PY_VERSION="3.8"  # default macos version
VENV=".venv"  # virtual environment

# ARGUMENT PARSING
# =============================================================================

HELP="usage: setup.sh [-h]

Set up a development environment.

Fetches full git history, updates git tags, installs Python and
sets up a virtual environment using \`uv\`.

options:
  -h|--help  Show this help message and exit."

if [ "$#" -eq 1 ] && { [ "$1" = "-h" ] || [ "$1" = "--help" ]; }; then
  echo "$HELP"
  exit 0
elif [ "$#" -gt 0 ]; then
  echo "$HELP" >&2
  exit 1
fi

# SCRIPT
# =============================================================================

# fetch full git history
if [ -f .git/shallow ]; then
  echo "Fetching full git history..."
  git fetch --unshallow
fi

# ensure git is up to date
echo "pruning and fetching tags..."
git fetch --all --tags --prune

uv python install $PY_VERSION
uv venv $VENV --python $PY_VERSION
