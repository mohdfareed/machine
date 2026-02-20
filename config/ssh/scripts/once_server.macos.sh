#!/usr/bin/env bash
set -Eeuo pipefail
# Enable the SSH server on macOS.

echo "enabling ssh server..."
sudo systemsetup -setremotelogin on >/dev/null
