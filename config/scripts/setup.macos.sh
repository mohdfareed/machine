#!/usr/bin/env bash

echo "setting up macos..."

# Check if SSH server is already enabled
if sudo systemsetup -getremotelogin | grep -q "On"; then
  echo "ssh server is already enabled"
  exit 0
fi

# Enable SSH server
echo "enabling ssh server..."
sudo systemsetup -setremotelogin on
echo "ssh server enabled successfully"

echo "macos set up successfully"
