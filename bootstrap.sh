#!/usr/bin/env sh
set -eu

# Bootstrap: curl -LsSf https://raw.githubusercontent.com/mohdfareed/machine/main/bootstrap.sh | sh
# Requires: git, curl

REPO="${MC_ROOT:-$HOME/.machine}"
UV_TMP="${TMPDIR:-/tmp}/uv-bootstrap"
UV=""

# ensure uv is available
if command -v uv >/dev/null 2>&1; then
    UV="uv"
else
    curl -LsSf https://astral.sh/uv/install.sh | env UNMANAGED_INSTALL="$UV_TMP" sh
    UV="$UV_TMP/uv"
fi

# clone repo if needed
[ -d "$REPO/.git" ] || git clone https://github.com/mohdfareed/machine.git "$REPO"

# install the cli tool
"$UV" tool install "$REPO" --force

# clean up temp uv
[ "$UV" = "uv" ] || rm -rf "$UV_TMP"

echo "Done. Run 'mc --help' to get started."
