#!/usr/bin/env bash

# set hostname
echo "setting hostname..."
sudo scutil --set LocalHostName "$MACHINE_ID"

# enable SSH server
echo "enabling ssh server..."
sudo systemsetup -setremotelogin on >/dev/null
