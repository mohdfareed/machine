#!/bin/bash

echo "enabling ssh server..."

# Enable SSH server
sudo systemsetup -setremotelogin on

# Start SSH service
daemon=/System/Library/LaunchDaemons/ssh.plist
sudo launchctl load -w $daemon 2>/dev/null || true

echo "ssh server enabled successfully"
