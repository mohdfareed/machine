#!/usr/bin/env bash
set -Eeuo pipefail

# set hostname
target_hostname="${MC_HOSTNAME:-$MC_ID}"
if [[ -n "$target_hostname" && "$(hostname)" != "$target_hostname" ]]; then
    echo "setting hostname..."
    if command -v hostnamectl &>/dev/null; then
        sudo hostnamectl set-hostname "$target_hostname"
    else
        sudo hostname "$target_hostname"
        echo "$target_hostname" | sudo tee /etc/hostname >/dev/null
    fi
fi

# enable hush login
[ -f "$HOME/.hushlogin" ] || touch "$HOME/.hushlogin"
