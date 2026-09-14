#!/usr/bin/env bash
set -Eeuo pipefail

# Preserve existing access memberships while allowing administrators.
echo "allowing administrators remote login..."
if ! dscl . -read /Groups/com.apple.access_ssh >/dev/null 2>&1; then
    sudo dseditgroup -o create -n . com.apple.access_ssh
fi
sudo dseditgroup -o edit -n . -a admin -t group com.apple.access_ssh

echo "enabling ssh server..."
sudo systemsetup -setremotelogin on
