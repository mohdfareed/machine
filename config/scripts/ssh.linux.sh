#!/usr/bin/env bash

echo "settings up ssh server..."

# check if ssh server is already active
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

echo "ssh server enabled successfully"
