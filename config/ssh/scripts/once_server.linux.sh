#!/usr/bin/env bash
set -Eeuo pipefail
# Install and enable the SSH server on Linux.

echo "installing ssh server..."
sudo apt-get update -y
sudo apt-get install -y openssh-server

echo "configuring ssh server..."
sudo systemctl enable ssh
sudo systemctl start ssh
