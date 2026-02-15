#!/usr/bin/env sh
set -eu

# Bootstrap: curl -LsSf https://raw.githubusercontent.com/mohdfareed/machine/main/bootstrap.sh | sh
ROOT="${MC_ROOT:-$HOME/.machine}"

# ensure git and uv are available
if ! command -v git >/dev/null 2>&1; then
    echo "Error: git is not installed. Please install git and try again."
    exit 1
fi
if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# clone repo if needed
[ -d "$ROOT/.git" ] || git clone https://github.com/mohdfareed/machine.git "$ROOT"

# install the cli tool
uv tool install "$ROOT" --force
echo "Done. Run 'mc --help' to get started."
