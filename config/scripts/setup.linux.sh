#!/usr/bin/env zsh

echo "updating linux tools..."


sudo chsh -s "$(which zsh)" "$USER"

sudo apt update && sudo apt full-upgrade -y
sudo apt autoremove -y

if command -v snap &>/dev/null; then
    snap refresh
fi

echo "linux tools updated successfully"
