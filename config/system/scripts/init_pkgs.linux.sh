#!/usr/bin/env bash
set -Eeuo pipefail

# setup apt
echo "setting up apt..."
sudo apt update -y
sudo apt autoremove -y

# setup snap
echo "setting up snap..."
sudo apt install snapd -y
sudo snap refresh
