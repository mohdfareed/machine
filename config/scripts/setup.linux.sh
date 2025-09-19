#!/usr/bin/env bash

# set hostname
echo "setting hostname..."
if command -v hostnamectl &> /dev/null; then
    sudo hostnamectl set-hostname "$MACHINE_ID"
else
    sudo hostname "$MACHINE_ID"
    echo "$MACHINE_ID" | sudo tee /etc/hostname > /dev/null
fi

# check if ssh server is already active
echo "settings up ssh server..."
if systemctl is-active --quiet ssh; then
    echo "ssh server is already enabled"
    exit 0
fi

# install ssh server
echo "installing ssh server..."
sudo apt install -y openssh-server
echo "configuring ssh server..."
sudo systemctl enable ssh
sudo systemctl start ssh
