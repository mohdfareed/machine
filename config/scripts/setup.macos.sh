#!/bin/bash

echo "setting up macos..."

# Check if SSH server is already enabled
if sudo systemsetup -getremotelogin | grep -q "On"; then
  echo "ssh server is already enabled"
  exit 0
fi

# Enable SSH server
echo "enabling ssh server..."
sudo systemsetup -setremotelogin on

# Start SSH service
daemon=/System/Library/LaunchDaemons/ssh.plist
sudo launchctl load -w $daemon 2>/dev/null || true
echo "ssh server enabled successfully"


echo "macos set up successfully"
