#!/usr/bin/env bash
set -Eeuo pipefail

if ! command -v tailscale &>/dev/null; then
    echo "tailscale not found, skipping"
    exit 0
fi

# Connect if not already connected (interactive auth on first run).
if ! tailscale status &>/dev/null; then
    echo "connecting to tailscale..."
    sudo tailscale up
fi

echo "configuring tailscale serve (Homepage dashboard)..."
sudo tailscale serve --bg http://127.0.0.1:3000
tailscale serve status
