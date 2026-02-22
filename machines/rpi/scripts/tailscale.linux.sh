#!/usr/bin/env bash
set -Eeuo pipefail

# Configure Tailscale for RPi server use.

if ! command -v tailscale &>/dev/null; then
    echo "tailscale not found, skipping"
    exit 0
fi

# Connect if not already connected (interactive auth on first run).
if ! tailscale status &>/dev/null; then
    echo "connecting to tailscale..."
    sudo tailscale up
fi

tailscale status
echo "status:"
tailscale status
