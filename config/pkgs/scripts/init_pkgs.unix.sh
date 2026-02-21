#!/usr/bin/env bash
set -Eeuo pipefail

export NONINTERACTIVE=1

if command -v brew &>/dev/null; then
    echo "updating brew..."
    brew update
    brew cleanup --prune=all
    brew services cleanup
else
    echo "installing brew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

if command -v apt &>/dev/null; then
    echo "setting up apt..."
    sudo apt update -y
    sudo apt autoremove -y
    sudo apt install -y snapd
fi

if command -v snap &>/dev/null; then
    echo "setting up snap..."
    sudo snap refresh
fi
