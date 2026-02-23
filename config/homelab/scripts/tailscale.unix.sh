#!/usr/bin/env bash
set -Eeuo pipefail

# Configure Tailscale for homelab use.

case "${MC_HOMELAB_TUNNEL:-}" in
  true|1|yes|y) enable=true ;;
  *) enable=false ;;
esac

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

echo "resetting stale tailscale serve config..."
sudo tailscale serve reset

echo "configuring tailscale serve (HTTPS, tailnet-only)..."
sudo tailscale serve --bg http://127.0.0.1:7880

if [[ "$enable" == true ]]; then
  echo "configuring tailscale funnel (public internet, port 8443)..."
  sudo tailscale funnel --bg --https=8443 http://127.0.0.1:7881
fi

tailscale funnel status
