#!/usr/bin/env bash
set -Eeuo pipefail

# Configure Tailscale for homelab server use.

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

# ─── Tailscale Funnel ─────────────────────────────────────────────────────────
# Expose only the webhook paths via Funnel (public HTTPS).
# The OpenClaw Control UI stays tailnet-only at http://homelab:18789.
echo "configuring tailscale funnel for webhooks..."
sudo tailscale serve --bg --set-path /openclaw/telegram http://127.0.0.1:18789
sudo tailscale serve --bg --set-path /openclaw/hooks http://127.0.0.1:18789
