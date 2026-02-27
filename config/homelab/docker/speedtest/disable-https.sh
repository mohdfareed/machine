#!/bin/bash
# Disable nginx HTTPS — Tailscale sidecar handles TLS on :443.
# Without this, nginx tries to bind 0.0.0.0:443 which conflicts
# with Tailscale Serve in the shared network namespace.

CONF="/config/nginx/site-confs/default.conf"
[ -f "$CONF" ] || exit 0

# Comment out all listen 443 and ssl_ directives
sed -i '/^\s*listen.*443/s/^/#/' "$CONF"
sed -i '/^\s*ssl_certificate/s/^/#/' "$CONF"

echo "[disable-https] Nginx HTTPS listener disabled."
