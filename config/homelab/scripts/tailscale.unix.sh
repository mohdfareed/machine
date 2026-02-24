#!/usr/bin/env bash
set -Eeuo pipefail

# Connect the host to Tailscale.
# Individual Docker services use Tailscale sidecars for their own host names.
# Machine-specific tailscale serve/funnel config lives in machines/<id>/scripts/.

if ! command -v tailscale &>/dev/null; then
    echo "tailscale not found, skipping"
    exit 0
fi

# Connect if not already connected (interactive auth on first run).
if ! tailscale status &>/dev/null; then
    echo "connecting to tailscale..."
    sudo tailscale up
fi
