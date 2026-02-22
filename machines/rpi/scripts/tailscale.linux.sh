#!/usr/bin/env bash
set -Eeuo pipefail

# Configure Tailscale for RPi server use.
# Uses `tailscale set` (imperative) instead of the frozen `tailscale up`.

if ! command -v tailscale &>/dev/null; then
    echo "tailscale not found, skipping"
    exit 0
fi

# Connect if not already connected (interactive auth on first run).
if ! tailscale status &>/dev/null; then
    echo "connecting to tailscale..."
    sudo tailscale up
fi

echo "configuring tailscale..."

# Enable Tailscale SSH and accept routes (defaults false on Linux).
sudo tailscale set --ssh --accept-routes

echo "tailscale configured."
tailscale status
