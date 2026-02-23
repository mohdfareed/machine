#!/usr/bin/env bash
set -Eeuo pipefail

# Homelab-specific Tailscale Funnel setup.
# The shared tailscale.unix.sh (from the homelab module) handles serve.
# This script adds public funnel routes for webhooks.

if ! command -v tailscale &>/dev/null; then
    echo "tailscale not found"
    exit 1
fi

# ─── Tailscale Funnel ────────────────────────────────────────────────────────
# Traefik handles path routing + prefix stripping.
#   funnel (:8443) → Traefik :7881 (public, internet-facing webhooks)

echo "resetting stale tailscale funnel config..."
sudo tailscale funnel reset

echo "configuring tailscale funnel (public internet, port 8443)..."
sudo tailscale funnel --bg --https=8443 http://127.0.0.1:7881
