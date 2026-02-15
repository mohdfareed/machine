#!/usr/bin/env sh
set -eu

# Bootstrap: curl -LsSf https://raw.githubusercontent.com/mohdfareed/machine/main/bootstrap.sh | sh
ROOT="${MC_ROOT:-$HOME/.machine}"
UV="uv"
TMP_DIR=""

# clone repo if needed
if ! [ -d "$ROOT/.git" ]; then
    git clone https://github.com/mohdfareed/machine.git "$ROOT"
fi

# ensure uv is available
if ! command -v uv >/dev/null 2>&1; then
    TMP_DIR=$(mktemp -d)
    export UV_INSTALL_DIR="$TMP_DIR"
    export UV_NO_MODIFY_PATH=1
    export UV_DISABLE_UPDATE=1

    # install uv to temp dir
    curl -LsSf https://astral.sh/uv/install.sh | sh
    UV="$TMP_DIR/uv"
    bin="$("$UV" tool dir --bin)"
    export PATH="$bin:$PATH"
fi

# install the cli tool
"$UV" tool install "$ROOT" --force
[ -n "$TMP_DIR" ] && rm -rf "$TMP_DIR" # clean up
echo "Done. Run 'mc --help' to get started."
