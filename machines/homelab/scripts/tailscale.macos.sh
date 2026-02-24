#!/usr/bin/env bash
set -Eeuo pipefail

# Homelab-specific Tailscale cleanup.
# Resets any stale funnel config (per-service sidecars handle their own).

if ! command -v tailscale &>/dev/null; then
    echo "tailscale not found"
    exit 1
fi

echo "resetting stale tailscale funnel config..."
sudo tailscale funnel reset 2>/dev/null || true
