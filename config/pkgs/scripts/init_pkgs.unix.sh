#!/usr/bin/env bash
set -Eeuo pipefail

export NONINTERACTIVE=1

if ! command -v brew &>/dev/null; then
    echo "installing brew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

if command -v apt &>/dev/null; then
    echo "setting up apt..."
    sudo apt update -y
fi

if command -v snap &>/dev/null; then
    echo "setting up snap..."
    sudo snap refresh
elif command -v apt &>/dev/null; then
    echo "installing snap..."
    sudo apt install -y snapd
fi
