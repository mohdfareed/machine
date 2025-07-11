#!/usr/bin/env zsh

echo "setting up linux..."

sudo chsh -s "$(which zsh)" "$USER"

sudo apt update -y
sudo apt autoremove -y

echo "linux set up successfully"
