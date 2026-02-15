#!/usr/bin/env sh
set -eu

export MC_HOME="${MC_HOME:-$HOME/.machine}"
UV="uv"; TMP_DIR="" # temp uv installation

# Ensure uv is available
if ! command -v uv >/dev/null 2>&1; then
    TMP_DIR=$(mktemp -d)
    cleanup() { [ -n "$TMP_DIR" ] && rm -rf "$TMP_DIR"; }
    trap cleanup EXIT # cleanup temp dir on exit

    export UV_INSTALL_DIR="$TMP_DIR"
    export UV_NO_MODIFY_PATH=1
    export UV_DISABLE_UPDATE=1

    # Install uv to temp dir
    curl -LsSf https://astral.sh/uv/install.sh | sh
    UV="$TMP_DIR/uv"
fi

# Clone repo if needed
if ! [ -d "$MC_HOME/.git" ]; then
    git clone https://github.com/mohdfareed/machine.git "$MC_HOME"
fi

# Install the cli tool
"$UV" tool install "$MC_HOME" --editable --force
MC="$(cd "$("$UV" tool dir --bin)" && pwd)/mc"
echo "Installed machine cli to $MC"
