#!/usr/bin/env bash
set -Eeuo pipefail

# https://<machine>.<tailnet>.ts.net → localhost:3000 (Homepage)

if ! command -v tailscale &>/dev/null; then
    echo "tailscale not found"
    exit 1
fi

echo "configuring tailscale serve (Homepage dashboard)..."
sudo tailscale serve --bg http://127.0.0.1:3000
tailscale serve status
