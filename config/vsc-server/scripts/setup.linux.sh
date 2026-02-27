#!/usr/bin/env bash
set -Eeuo pipefail

# Install code serve-web as a systemd user service and expose via tailscale serve.
# Access: https://<machine>.<tailnet>.ts.net/code

VSC_PORT=12345
SERVICE_NAME="mc-vsc-server"

if ! command -v code &>/dev/null; then
    echo "code not found, skipping vsc-server setup"
    exit 0
fi

# ─── Systemd user service ────────────────────────────────────────────────────

UNIT_DIR="$HOME/.config/systemd/user"
UNIT_FILE="$UNIT_DIR/$SERVICE_NAME.service"
mkdir -p "$UNIT_DIR"

CODE_BIN="$(command -v code)"

cat > "$UNIT_FILE" <<EOF
[Unit]
Description=VS Code Server (serve-web)
After=network.target

[Service]
Type=exec
ExecStart=$CODE_BIN serve-web --port $VSC_PORT --server-base-path /code --without-connection-token --accept-server-license-terms
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now "$SERVICE_NAME"
echo "vsc-server: systemd service started on port $VSC_PORT"

# ─── Tailscale serve ─────────────────────────────────────────────────────────

if command -v tailscale &>/dev/null; then
    echo "configuring tailscale serve for vsc-server..."
    sudo tailscale serve --bg --set-path /code http://127.0.0.1:$VSC_PORT
fi
