#!/usr/bin/env sh
set -eu

# Create a bootstrap temporary directory.
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

# ═════════════════════════════════════════════════════════════════════════════
# Args Parsing
# ═════════════════════════════════════════════════════════════════════════════

# Select optional deployment.
deploy=false
case "${MC_BOOTSTRAP_DEPLOY:-}" in
    1 | true) deploy=true ;;
esac
case "${1-}" in
    --deploy | -d) deploy=true ;;
    "--help" | "-h")
        echo "Usage: $0 [options]"
        echo "Options:"
        echo "  --deploy, -d    Deploy the machine after bootstrap"
        echo "  --help,   -h    Show this help message"
        exit 0
        ;;
    "") ;;
    *) echo "Unknown option: $1" >&2 && exit 1 ;;
esac

# ═════════════════════════════════════════════════════════════════════════════
# Dependencies
# ═════════════════════════════════════════════════════════════════════════════

# Ensure git is available
if ! command -v git >/dev/null 2>&1; then
  if [ "$(uname)" = "Darwin" ]; then
    echo "Error: git is not installed. Install Xcode CLT and try again." >&2
    xcode-select --install
    exit 1
  elif ! command -v apt >/dev/null 2>&1; then
    echo "Error: git is not installed. Install git and try again." >&2
    exit 1
  fi

  echo "Installing git..."
  sudo apt update && sudo apt install git
fi

# Ensure uv is available.
if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | \
  UV_INSTALL_DIR="$tmpdir" UV_NO_MODIFY_PATH=1 sh
  export PATH="$tmpdir:$PATH"
fi

# ═════════════════════════════════════════════════════════════════════════════
# Initialization
# ═════════════════════════════════════════════════════════════════════════════

# Resolve machine repo directory.
MC_HOME="$(eval echo "${MC_HOME:-$HOME/.machine}")"
export MC_HOME

# Resolve python version from .python-version file if it exists.
repo="https://raw.githubusercontent.com/mohdfareed/machine/main"
python_version=$(curl -LsSf $repo/.python-version)

# ═════════════════════════════════════════════════════════════════════════════
# Bootstrap
# ═════════════════════════════════════════════════════════════════════════════

# Install system dependencies.
if ! uv python list --only-installed | grep -q "$python_version"; then
  echo "Installing Python $python_version..."
  uv python install "$python_version"
fi

# Clone repo if needed.
if ! [ -d "$MC_HOME/.git" ]; then
  echo "Cloning machine repo to $MC_HOME..."
  git clone https://github.com/mohdfareed/machine.git "$MC_HOME"
fi

# Sync the repo and install the CLI.
uv run --project "$MC_HOME" mc sync

# Deploy only when requested.
if [ "$deploy" = true ]; then
  uv run --project "$MC_HOME" mc deploy
fi
