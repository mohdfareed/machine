#!/usr/bin/env bash
set -Eeuo pipefail

# RPi-specific Tailscale serve config.
# Per-service sidecars handle their own hostnames; this configures the
# machine's own HTTPS URL to serve Homepage.
#   https://rpi.<tailnet>.ts.net → localhost:3000 (Homepage)

if ! command -v tailscale &>/dev/null; then
    echo "tailscale not found"
    exit 1
fi

echo "resetting stale tailscale serve config..."
sudo tailscale serve reset

echo "configuring tailscale serve (Homepage dashboard)..."
sudo tailscale serve --bg http://127.0.0.1:3000
tailscale serve status
