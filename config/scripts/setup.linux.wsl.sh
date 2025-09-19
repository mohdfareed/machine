#!/usr/bin/env bash
set -Eeuo pipefail

# set zsh as default shell
echo "setting default shell to zsh..."
sudo chsh -s "$(command -v zsh)" "$USER"

# setup apt
echo "setting up apt..."
sudo apt update -y
sudo apt autoremove -y
