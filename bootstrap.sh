#!/usr/bin/env sh
set -eu

# Bootstrap: curl -LsSf https://raw.githubusercontent.com/mohdfareed/machine/main/bootstrap.sh | sh
# Requires: git, curl

REPO="${MC_ROOT:-$HOME/.machine}"

# ensure uv is available
if ! command -v uv >/dev/null 2>&1; then
    echo "uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "uv installed. Please run this script again."
    exit 1
fi

# clone repo if needed
[ -d "$REPO/.git" ] || git clone https://github.com/mohdfareed/machine.git "$REPO"

# install the cli tool
uv tool install "$REPO" --force

echo "Done. Run 'mc --help' to get started."
