#!/bin/sh
set -eu

if ! command -v /usr/local/bin/tailscale >/dev/null 2>&1; then
    echo "tailscale not found"
    exit 1
fi

# Connect if not already connected (interactive auth on first run).
if ! /usr/local/bin/tailscale status >/dev/null 2>&1; then
    echo "connecting to tailscale..."
    sudo /usr/local/bin/tailscale up
fi
