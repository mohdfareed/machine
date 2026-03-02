#!/usr/bin/env bash
set -Eeuo pipefail

# set hostname
HOSTNAME="${MC_HOSTNAME:-$MC_ID}"
if [[ -n "$HOSTNAME" ]]; then
    echo "setting hostname..."
    if command -v hostnamectl &>/dev/null; then
        sudo hostnamectl set-hostname "$HOSTNAME"
    else
        sudo hostname "$HOSTNAME"
        echo "$HOSTNAME" | sudo tee /etc/hostname >/dev/null
    fi
fi

# set zsh as default shell (linux)
echo "setting default shell to zsh..."
sudo chsh -s "$(command -v zsh)" "$USER"

# enable hush login
[ -f "$HOME/.hushlogin" ] || touch "$HOME/.hushlogin"
