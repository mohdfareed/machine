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

echo "status:"
tailscale status

# ─── Tailscale Serve ─────────────────────────────────────────────────────────
# HTTPS reverse proxy (tailnet-only, valid Let's Encrypt cert).
# All services bind loopback-only; Tailscale Serve is the sole gateway.

echo "resetting stale tailscale serve config..."
sudo tailscale serve reset

echo "configuring tailscale serve (HTTPS, tailnet-only)..."
sudo tailscale serve --bg --set-path / http://127.0.0.1:3000  # homepage (dashboard)
