#!/usr/bin/env bash

echo "setting up linux/wsl..."

# Set zsh as default shell
sudo chsh -s "$(which zsh)" "$USER"

# Cleanup apt
sudo apt autoremove -y

echo "linux/wsl set up successfully"
