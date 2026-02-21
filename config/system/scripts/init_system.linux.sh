#!/usr/bin/env bash
set -Eeuo pipefail

# set hostname
echo "setting hostname..."
if command -v hostnamectl &> /dev/null; then
  sudo hostnamectl set-hostname "$MC_NAME"
else
  sudo hostname "$MC_NAME"
  echo "$MC_NAME" | sudo tee /etc/hostname > /dev/null
fi

# set zsh as default shell
if command -v zsh &>/dev/null; then
  echo "setting default shell to zsh..."
  sudo chsh -s "$(command -v zsh)" "$USER"
fi
