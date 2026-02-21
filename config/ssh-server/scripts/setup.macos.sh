#!/usr/bin/env bash
set -Eeuo pipefail

echo "enabling ssh server..."
sudo systemsetup -setremotelogin on
