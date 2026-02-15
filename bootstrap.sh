#!/usr/bin/env sh
set -eu

export MC_HOME="${MC_HOME:-$HOME/.machine}"
BIN="$HOME/.local/bin"

# Ensure ~/.local/bin is on PATH for next shell
if ! echo "$PATH" | tr ':' '\n' | grep -qx "$BIN"; then
    # shellcheck disable=SC1091
    if [ -f "$HOME/.zshenv" ] && . "$HOME/.zshenv" 2>/dev/null &&
       echo "$PATH" | tr ':' '\n' | grep -qx "$BIN"; then
        : # already defined in .zshenv
    else
        # shellcheck disable=SC2016
        echo >> "$HOME/.zshenv"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshenv"
        echo >> "$HOME/.zshenv"
    fi
fi

# Ensure uv is available
if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | UV_NO_MODIFY_PATH=1 sh
    echo "uv installed. Restart shell and re-run this script."
    exit 0
fi

# Clone repo if needed
if ! [ -d "$MC_HOME/.git" ]; then
    git clone https://github.com/mohdfareed/machine.git "$MC_HOME"
fi

# Install the cli tool
uv tool install "$MC_HOME" --editable --force
echo "Installed machine cli. Restart shell and run 'mc --help' for more info."
