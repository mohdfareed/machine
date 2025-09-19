#!/usr/bin/env bash
set -Eeuo pipefail

if [[ -z ${MACHINE_ID:-} ]]; then
    echo "MACHINE_ID is not set; skipping hostname configuration" >&2
else
    # set hostname
    echo "setting hostname..."
    if command -v hostnamectl &> /dev/null; then
        sudo hostnamectl set-hostname "$MACHINE_ID"
    else
        sudo hostname "$MACHINE_ID"
        echo "$MACHINE_ID" | sudo tee /etc/hostname > /dev/null
    fi
fi

echo "settings up ssh server..."
if ! dpkg -s openssh-server >/dev/null 2>&1; then
    echo "installing ssh server..."
    sudo apt-get update -y
    sudo apt-get install -y openssh-server
fi
echo "configuring ssh server..."
sudo systemctl enable ssh || true
sudo systemctl start ssh || true
if systemctl is-active --quiet ssh; then
    echo "ssh server is active"
else
    echo "warning: ssh server not active" >&2
fi
