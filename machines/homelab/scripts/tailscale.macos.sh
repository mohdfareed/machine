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
# serve: HTTPS reverse proxy (tailnet-only, valid Let's Encrypt cert).
#   All services bind loopback-only; Tailscale Serve is the sole gateway.
# funnel: makes specific paths publicly reachable from the internet.

echo "resetting stale tailscale serve/funnel config..."
sudo tailscale serve reset
sudo tailscale funnel reset

echo "configuring tailscale serve (HTTPS, tailnet-only)..."
sudo tailscale serve --bg --set-path /              http://127.0.0.1:3000   # homepage (dashboard)
sudo tailscale serve --bg --set-path /portainer      http://127.0.0.1:9000   # portainer
sudo tailscale serve --bg --set-path /openclaw       http://127.0.0.1:18789  # openclaw
sudo tailscale serve --bg --set-path /kbm/personal   http://127.0.0.1:8001   # kbm personal
sudo tailscale serve --bg --set-path /kbm/work       http://127.0.0.1:8002   # kbm work
sudo tailscale serve --bg --set-path /kbm/private    http://127.0.0.1:8003   # kbm private

echo "configuring tailscale funnel (public internet)..."
sudo tailscale funnel --bg --set-path /openclaw/telegram http://127.0.0.1:18789  # telegram webhook
