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

# ─── Tailscale Serve / Funnel ────────────────────────────────────────────────
# serve: HTTPS reverse proxy (tailnet-only) — fixes browser secure context requirement.
# funnel: makes only the Telegram webhook path public (Telegram needs to reach it).
echo "configuring tailscale serve/funnel for openclaw..."
sudo tailscale serve --bg --set-path /openclaw http://127.0.0.1:18789
sudo tailscale funnel --bg --set-path /openclaw/telegram http://127.0.0.1:18789
