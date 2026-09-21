#!/usr/bin/env zsh
set -Eeuo pipefail

echo "configuring tailscale serve (Dashboard)..."
sudo tailscale serve --bg http://127.0.0.1:3000
tailscale serve status
