#!/bin/bash
# Enable SSH server on macOS

echo "Enabling SSH server..."

# Enable SSH server
sudo systemsetup -setremotelogin on

# Start SSH service
sudo launchctl load -w /System/Library/LaunchDaemons/ssh.plist 2>/dev/null || true

echo "SSH server enabled successfully"
