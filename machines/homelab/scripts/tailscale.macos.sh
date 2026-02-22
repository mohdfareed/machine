#!/usr/bin/env bash
set -Eeuo pipefail

# Configure Tailscale for homelab server use.
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

# Enable Tailscale SSH (access via `ssh homelab` over tailnet).
# --accept-routes defaults to true on macOS, so not needed here.
sudo tailscale set --ssh

echo "tailscale configured."
tailscale status
echo "status:"
tailscale status
