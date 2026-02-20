#!/usr/bin/env bash
set -Eeuo pipefail

if [[ -z ${MC_ID:-} ]]; then
    echo "MC_ID is not set; skipping hostname configuration" >&2
else
    # set hostname
    echo "setting hostname..."
    if command -v hostnamectl &> /dev/null; then
        sudo hostnamectl set-hostname "$MC_ID"
    else
        sudo hostname "$MC_ID"
        echo "$MC_ID" | sudo tee /etc/hostname > /dev/null
    fi
fi
