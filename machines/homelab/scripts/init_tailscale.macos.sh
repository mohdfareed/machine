#!/usr/bin/env bash
set -Eeuo pipefail

# Configure Tailscale for homelab server use.

if ! command -v tailscale &>/dev/null; then
    echo "tailscale not found, skipping"
    exit 0
fi

echo "configuring tailscale..."

# Enable Tailscale SSH (access via `ssh homelab` over tailnet).
# Accept routes from other nodes and advertise this machine as a subnet router.
sudo tailscale up \
    --ssh \
    --accept-routes \
    --operator="$USER"

echo "tailscale configured."
echo "status:"
tailscale status
