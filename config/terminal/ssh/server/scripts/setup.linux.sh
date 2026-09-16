#!/usr/bin/env bash
set -Eeuo pipefail

echo "configuring ssh server..."
sudo systemctl enable ssh
sudo systemctl start ssh
