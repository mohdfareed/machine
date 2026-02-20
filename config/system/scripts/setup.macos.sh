#!/usr/bin/env bash
set -Eeuo pipefail

# set hostname
if [[ -z ${MC_ID:-} ]]; then
	echo "MC_ID is not set; skipping hostname configuration" >&2
else
	echo "setting hostname..."
    sudo scutil --set LocalHostName "$MC_ID"
fi
