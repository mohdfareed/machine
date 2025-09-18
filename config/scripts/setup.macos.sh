#!/usr/bin/env bash

echo "setting up macos..."

# set hostname
echo "setting hostname..."
sudo scutil --set LocalHostName "$MACHINE_ID"

# enable SSH server
echo "enabling ssh server..."
sudo systemsetup -setremotelogin on >/dev/null

echo "macos set up successfully"
