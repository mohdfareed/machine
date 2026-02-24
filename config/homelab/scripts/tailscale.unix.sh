#!/usr/bin/env bash
set -Eeuo pipefail

# Configure Tailscale for homelab use.
# Connects the machine and serves Homepage on the machine's HTTPS URL.
# Individual Docker services use Tailscale sidecars for their own host names.

if ! command -v tailscale &>/dev/null; then
    echo "tailscale not found, skipping"
    exit 0
fi

# Connect if not already connected (interactive auth on first run).
if ! tailscale status &>/dev/null; then
    echo "connecting to tailscale..."
    sudo tailscale up
fi

# ─── Tailscale Serve ─────────────────────────────────────────────────────────
# Serve Homepage dashboard on the machine's HTTPS URL.
#   https://<machine>.<tailnet>.ts.net → localhost:3000 (Homepage)

echo "resetting stale tailscale serve config..."
sudo tailscale serve reset

echo "configuring tailscale serve (Homepage dashboard)..."
sudo tailscale serve --bg http://127.0.0.1:3000

tailscale serve status
