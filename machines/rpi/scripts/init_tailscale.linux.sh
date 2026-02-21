#!/usr/bin/env bash
set -Eeuo pipefail

# Configure Tailscale for RPi server use.

if ! command -v tailscale &>/dev/null; then
    echo "tailscale not found, skipping"
    exit 0
fi

echo "configuring tailscale..."

sudo tailscale up \
    --ssh \
    --accept-routes \
    --operator="$USER"

echo "tailscale configured."
echo "status:"
tailscale status
