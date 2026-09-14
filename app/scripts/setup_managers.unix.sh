#!/usr/bin/env bash
set -Eeuo pipefail

export NONINTERACTIVE=1
managers=" ${MC_PKG_MANAGERS-} "

# brew
if [[ " $managers " == *" brew "* ]]; then
    source "$(dirname "${BASH_SOURCE[0]}")/environment.unix.sh"
    if ! command -v brew &>/dev/null; then
        installer="$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        /bin/bash -c "$installer"
        source "$(dirname "${BASH_SOURCE[0]}")/environment.unix.sh"
    fi

    if ! command -v brew &>/dev/null; then
        echo "Homebrew installation did not make brew available" >&2
        exit 1
    fi
fi

# mas
if [[ "$managers" == *" mas "* ]] && ! command -v mas &>/dev/null; then
    echo "installing mas..."
    brew install mas
fi

# snap
if [[ "$managers" == *" snap "* ]] && ! command -v snap &>/dev/null; then
    echo "installing snap..."
    sudo apt update -y
    sudo apt install -y snapd
fi
