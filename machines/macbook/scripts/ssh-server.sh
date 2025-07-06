#!/bin/bash

echo "enabling ssh server..."

# Enable SSH server
sudo systemsetup -setremotelogin on
# Start SSH service
sudo launchctl load -w /System/Library/LaunchDaemons/ssh.plist 2>/dev/null || true

echo "ssh server enabled successfully"
