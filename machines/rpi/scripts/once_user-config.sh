#!/usr/bin/env bash
set -Eeuo pipefail

echo "configuring rpi environment..."

# run user services without active login
sudo loginctl enable-linger "$USER"
# ensure ~/.config exists
mkdir -p "$HOME/.config"
chmod 755 "$HOME/.config"
