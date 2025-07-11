#!/bin/bash

# Check if SSH server is already enabled
if sudo systemsetup -getremotelogin | grep -q "On"; then
  echo "ssh server is already enabled"
  exit 0
fi

echo "enabling ssh server..."

# Enable SSH server
sudo systemsetup -setremotelogin on

# Start SSH service
daemon=/System/Library/LaunchDaemons/ssh.plist
sudo launchctl load -w $daemon 2>/dev/null || true

echo "ssh server enabled successfully"
