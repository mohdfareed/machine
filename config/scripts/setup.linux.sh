#!/usr/bin/env bash

echo "setting up linux..."

# Set hostname
echo "setting hostname..."
if command -v hostnamectl &> /dev/null; then
    sudo hostnamectl set-hostname "$MACHINE_ID"
else
    sudo hostname "$MACHINE_ID"
    echo "$MACHINE_ID" | sudo tee /etc/hostname > /dev/null
fi

echo "linux set up successfully"
