#!/usr/bin/env sh
set -eu

PY_VERSION=${PY_VERSION:-"3.8"}  # default macos version
VENV=${VENV:-".venv"}  # virtual environment path

HELP="""
usage: setup.sh [-h]

Set up a development environment.

Fetches full git history and tags, installs Python and sets up a
virtual environment using \`uv\`.

options:
  -h|--help   Show this help message and exit.

environment:
  PY_VERSION  Python version to install (using: $PY_VERSION)
  VENV        Path to the virtual environment (using: $VENV)

requirements:
  - git
  - uv
"""

# ARGUMENT PARSING
# =============================================================================

HELP="${HELP#?}"; HELP="${HELP%?}"
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
  echo "fetching full history..."
  git fetch --unshallow
fi

# ensure git is up to date
echo "updating repository..."
git fetch --all --tags --prune

# install python and setup venv
echo "setting up python $PY_VERSION venv..."
uv python install "$PY_VERSION"
uv venv "$VENV" --python "$PY_VERSION" --seed --clear

# install pre-commit hooks
echo "installing pre-commit hooks..."
"./$VENV/bin/python" -m pip install pre-commit
"./$VENV/bin/pre-commit" install --install-hooks
