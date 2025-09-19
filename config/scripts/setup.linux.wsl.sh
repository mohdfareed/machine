#!/usr/bin/env bash

# set zsh as default shell
echo "setting default shell to zsh..."
sudo chsh -s "$(which zsh)" "$USER"

# setup apt
echo "setting up apt..."
sudo apt update
sudo apt autoremove -y
