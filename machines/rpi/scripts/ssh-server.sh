#!/bin/bash

echo "enabling ssh server..."

# Enable and start SSH service
sudo systemctl enable ssh
sudo systemctl start ssh
# Configure SSH to start on boot
sudo systemctl enable ssh.service

echo "ssh server enabled successfully"
