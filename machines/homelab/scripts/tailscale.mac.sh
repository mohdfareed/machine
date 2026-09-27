#!/bin/sh
set -eu

if ! command -v tailscale >/dev/null 2>&1; then
    echo "tailscale not found, skipping"
    exit 1
fi

# Connect if not already connected (interactive auth on first run).
if ! tailscale status >/dev/null 2>&1; then
    echo "connecting to tailscale..."
    sudo tailscale up
fi
