#!/bin/sh
set -eu

echo "configuring ssh server..."
sudo systemctl enable ssh
sudo systemctl start ssh
