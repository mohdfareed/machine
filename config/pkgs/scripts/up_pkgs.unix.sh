#!/usr/bin/env bash
set -Eeuo pipefail

if command -v brew &>/dev/null; then
    echo "upgrading brew packages..."
    brew update
    brew upgrade
    brew upgrade --cask --greedy-latest
    brew autoremove
    brew cleanup --prune=all
    brew services cleanup
fi

if command -v mas &>/dev/null; then
    echo "upgrading App Store apps..."
    mas upgrade
fi

if command -v apt &>/dev/null; then
    echo "upgrading apt packages..."
    sudo apt update -y
    sudo apt upgrade -y
    sudo apt autoremove -y
fi

if command -v snap &>/dev/null; then
    echo "upgrading snap packages..."
    sudo snap refresh
fi
