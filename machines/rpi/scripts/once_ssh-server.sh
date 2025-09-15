#!/bin/bash

echo "enabling ssh server..."

# Enable and start SSH service
sudo apt install -y openssh-server
sudo systemctl enable ssh
sudo systemctl start ssh

echo "ssh server enabled successfully"
