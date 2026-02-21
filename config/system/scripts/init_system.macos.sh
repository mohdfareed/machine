#!/usr/bin/env bash
set -Eeuo pipefail

# set hostname
if [[ -z ${MC_NAME:-} ]]; then
  echo "MC_NAME is not set; skipping hostname configuration" >&2
else
  echo "setting hostname..."
  sudo scutil --set LocalHostName "$MC_NAME"
fi

# enable file sharing
echo "enabling file sharing..."
sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.smbd.plist

# enable screen sharing
echo "enabling screen sharing..."
sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.screensharing.plist
