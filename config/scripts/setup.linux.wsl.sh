#!/usr/bin/env bash

echo "setting up linux/wsl..."

# set zsh as default shell
sudo chsh -s "$(which zsh)" "$USER"

# cleanup apt
sudo apt autoremove -y

echo "linux/wsl set up successfully"
