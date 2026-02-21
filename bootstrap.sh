#!/usr/bin/env sh
set -eu

MC_HOME="$(eval echo "${MC_HOME:-$HOME/.machine}")"
export MC_HOME

# Ensure uv is available
if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | \
    UV_INSTALL_DIR="$HOME/.local/bin" UV_NO_MODIFY_PATH=1 sh

    # Ensure ~/.local/bin is in .zshenv for future sessions
    if [ -f "$HOME/.zshenv" ] && grep -q '\.local/bin' "$HOME/.zshenv"; then
        : # already configured
    else
        echo '# Machine bootstrapping bin' >> "$HOME/.zshenv"
        # shellcheck disable=SC2016
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshenv"
    fi

    # Make uv available in this session
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install system dependencies
if ! uv python list --installed | grep -q "3.14"; then
    echo "Installing Python 3.14..."
    uv python install 3.14
fi

# Clone repo if needed
if ! [ -d "$MC_HOME/.git" ]; then
    git clone https://github.com/mohdfareed/machine.git "$MC_HOME"
fi

# Install the cli tool
uv tool install "$MC_HOME" --editable --force
echo "Installed machine cli. Run 'mc --help' for more info."
