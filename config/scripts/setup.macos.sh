#!/usr/bin/env bash
set -Eeuo pipefail

# set hostname
if [[ -z ${MACHINE_ID:-} ]]; then
	echo "MACHINE_ID is not set; skipping hostname configuration" >&2
else
	echo "setting hostname..."
    sudo scutil --set LocalHostName "$MACHINE_ID"
fi

# enable SSH server
echo "enabling ssh server..."
sudo systemsetup -setremotelogin on >/dev/null
