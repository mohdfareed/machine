#!/usr/bin/env bash
set -Eeuo pipefail

# set hostname
if [[ -n "${MC_HOSTNAME:-}" ]]; then
    echo "setting hostname..."
    if command -v hostnamectl &>/dev/null; then
        sudo hostnamectl set-hostname "$MC_HOSTNAME"
    else
        sudo hostname "$MC_HOSTNAME"
        echo "$MC_HOSTNAME" | sudo tee /etc/hostname >/dev/null
    fi
fi

# set zsh as default shell (linux)
echo "setting default shell to zsh..."
sudo chsh -s "$(command -v zsh)" "$USER"

# enable hush login
[ -f "$HOME/.hushlogin" ] || touch "$HOME/.hushlogin"
