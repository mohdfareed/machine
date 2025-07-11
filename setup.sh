#!/usr/bin/env sh
set -eu

HELP="Usage: setup.sh [options]

Set up a development environment.

Options:
  -h, --help    Show this help message
"

# SCRIPT
# =============================================================================

PY_VERSION="3.8"  # default macos version
VENV=".venv"  # virtual environment

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
