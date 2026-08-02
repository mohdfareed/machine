#!/usr/bin/env sh
set -eu

tmpdir="$(mktemp -d)"

# Resolve machine repo directory
MC_HOME="$(eval echo "${MC_HOME:-$HOME/.machine}")"
export MC_HOME

# Ensure git is available
if ! command -v git >/dev/null 2>&1; then
    if command -v apt >/dev/null 2>&1; then
        echo "Installing git..."
        sudo apt update && sudo apt install -y git
    elif [[ "$(uname)" == "Darwin" ]]; then
        echo "Error: git is not installed. " >&2
        xcode-select --install
        echo "Install Xcode Command Line Tools and try again." >&2
        exit 1
    else
        echo "Error: git is not installed. Install git and try again." >&2
        exit 1
    fi
fi

# Ensure uv is available
if ! command -v uv >/dev/null 2>&1; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | \
    UV_INSTALL_DIR="$tmpdir" UV_NO_MODIFY_PATH=1 sh

    # Make uv available in this session
    export PATH="$tmpdir:$PATH"
else
    echo "Updating uv..."
    uv self update 2>/dev/null || true
fi

# Install system dependencies
if ! uv python list --only-installed | grep -q "3.14"; then
    echo "Installing Python 3.14..."
    uv python install 3.14
fi

# Clone repo if needed
if ! [ -d "$MC_HOME/.git" ]; then
    echo "Cloning machine repo to $MC_HOME..."
    git clone https://github.com/mohdfareed/machine.git "$MC_HOME"
fi

# Install the cli tool
echo "Installing machine cli..."
uv tool install "$MC_HOME" --editable --force

# cleanup
rm -rf "$tmpdir" 2>/dev/null || true
echo "Installed machine cli. Run 'mc --help' for more info."
