#!/usr/bin/env bash
set -Eeuo pipefail

managers=" ${MC_PACKAGE_MANAGERS-} "

if [[ "$managers" == *" brew "* ]]; then
    echo "upgrading brew packages..."
    brew update
    brew upgrade || true
    brew upgrade --cask --greedy-latest
    brew autoremove
    brew cleanup --prune=all
    brew services cleanup
fi

if [[ "$managers" == *" mas "* ]]; then
    echo "upgrading App Store apps..."
    mas upgrade
fi

if [[ "$managers" == *" apt "* ]]; then
    echo "upgrading apt packages..."
    sudo apt update -y
    sudo apt upgrade -y
    sudo apt autoremove -y
fi

if [[ "$managers" == *" snap "* ]]; then
    echo "upgrading snap packages..."
    sudo snap refresh
fi
