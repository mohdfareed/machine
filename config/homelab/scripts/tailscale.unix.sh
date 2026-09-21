#!/usr/bin/env zsh
set -Eeuo pipefail

if ! command -v tailscale &>/dev/null; then
    echo "tailscale not found, skipping"
    exit 1
fi

# Connect if not already connected (interactive auth on first run).
if ! tailscale status &>/dev/null; then
    echo "connecting to tailscale..."
    sudo tailscale up
fi
