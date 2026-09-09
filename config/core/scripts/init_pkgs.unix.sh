#!/usr/bin/env bash
set -Eeuo pipefail

export NONINTERACTIVE=1
managers=" ${MC_PACKAGE_MANAGERS-} "

# brew
if [[ "$managers" == *" brew "* ]]; then
    # Make the standard install locations available, including after a fresh install.
    export PATH="/opt/homebrew/bin:/usr/local/bin:/home/linuxbrew/.linuxbrew/bin:$PATH"
    if ! command -v brew &>/dev/null; then
        echo "installing brew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
fi

# mas
if [[ "$managers" == *" mas "* ]] && ! command -v mas &>/dev/null; then
    echo "installing mas..."
    brew install mas
fi

# apt
if [[ "$managers" == *" apt "* ]]; then
    echo "setting up apt..."
    sudo apt update -y
fi

# snap
if [[ "$managers" == *" snap "* ]]; then
    if command -v snap &>/dev/null; then
        echo "setting up snap..."
        sudo snap refresh
    else
        echo "installing snap..."
        sudo apt install -y snapd
    fi
fi
