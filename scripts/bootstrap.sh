#!/usr/bin/env sh
set -eu

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

# Select optional deployment.
deploy=false
case "${MC_BOOTSTRAP_DEPLOY:-}" in
    1 | true) deploy=true ;;
esac
case "${1-}" in
    --deploy | -d) deploy=true ;;
    "") ;;
    *) echo "Unknown option: $1" >&2 && exit 1 ;;
esac

# Resolve machine repo directory
MC_HOME="$(eval echo "${MC_HOME:-$HOME/.machine}")"
export MC_HOME

# Resolve python version from .python-version file if it exists
repo="https://raw.githubusercontent.com/mohdfareed/machine/main"
python_version=$(curl -LsSf $repo/.python-version)

# Ensure git is available
if ! command -v git >/dev/null 2>&1; then
    if command -v apt >/dev/null 2>&1; then
        # Install using apt if available
        echo "Installing git..."
        sudo apt update && sudo apt install -y git
    elif [ "$(uname)" = "Darwin" ]; then
        # Prompt to install Xcode CLT on macOS
        echo "Error: git is not installed. Install Xcode CLT and try again." >&2
        xcode-select --install
        exit 1
    else
        # Fail otherwise
        echo "Error: git is not installed. Install git and try again." >&2
        exit 1
    fi
fi

# Ensure uv is available
if ! command -v uv >/dev/null 2>&1; then
    # Install uv temporarily
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | \
    UV_INSTALL_DIR="$tmpdir" UV_NO_MODIFY_PATH=1 sh

    # Make uv available in this session
    export PATH="$tmpdir:$PATH"
else
    # Updating existing uv installation
    echo "Updating uv..."
    uv self update 2>/dev/null || true
fi

# Install system dependencies
if ! uv python list --only-installed | grep -q "$python_version"; then
    echo "Installing Python $python_version..."
    uv python install "$python_version"
fi

# Clone repo if needed
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
