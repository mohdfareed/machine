#!/usr/bin/env sh
set -eu

export MC_HOME="${MC_HOME:-$HOME/.machine}"

# Ensure uv is available
if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | \
    UV_INSTALL_DIR="$HOME/.local/bin" UV_NO_MODIFY_PATH=1 sh

    # Source .zshenv and export PATH for the current session
    # shellcheck disable=SC1091
    if [ -f "$HOME/.zshenv" ]; then
        env_path=$(. "$HOME/.zshenv" && echo "$PATH")
    else
        env_path="$PATH"
    fi

    # Check if $HOME/.local/bin is in PATH. If not, add it.
    if ! echo "$env_path" | tr ':' '\n' | grep -qx "$HOME/.local/bin"; then
        echo '# Machine bootstrapping bin' >> "$HOME/.zshenv"
        # shellcheck disable=SC2016
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshenv"
        echo "Added $HOME/.local/bin to PATH in .zshenv."
    fi

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
