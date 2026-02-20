#!/usr/bin/env bash
set -Eeuo pipefail

# setup apt
echo "setting up apt..."
sudo apt update -y
sudo apt autoremove -y

# set zsh as default shell (requires zsh to be installed)
if command -v zsh &>/dev/null; then
    echo "setting default shell to zsh..."
    sudo chsh -s "$(command -v zsh)" "$USER"
fi
