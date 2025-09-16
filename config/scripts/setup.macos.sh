#!/usr/bin/env bash

echo "setting up macos..."

# Enable SSH server
echo "enabling ssh server..."
sudo systemsetup -setremotelogin on >/dev/null
echo "ssh server enabled successfully"

echo "macos set up successfully"
