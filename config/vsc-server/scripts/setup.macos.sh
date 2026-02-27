#!/usr/bin/env bash
set -Eeuo pipefail

# Install code serve-web as a launchd user agent and expose via tailscale serve.
# Access: https://<machine>.<tailnet>.ts.net/code

VSC_PORT=12345
LABEL="com.mc.vsc-server"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST="$PLIST_DIR/$LABEL.plist"

if ! command -v code &>/dev/null; then
    echo "code not found, skipping vsc-server setup"
    exit 0
fi

CODE_BIN="$(command -v code)"
mkdir -p "$PLIST_DIR"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$CODE_BIN</string>
        <string>serve-web</string>
        <string>--port</string>
        <string>$VSC_PORT</string>
        <string>--server-base-path</string>
        <string>/code</string>
        <string>--without-connection-token</string>
        <string>--accept-server-license-terms</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/mc-vsc-server.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/mc-vsc-server.log</string>
</dict>
</plist>
EOF

# Load (or reload) the agent.
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "vsc-server: launchd agent started on port $VSC_PORT"

# ─── Tailscale serve ─────────────────────────────────────────────────────────

if command -v tailscale &>/dev/null; then
    echo "configuring tailscale serve for vsc-server..."
    sudo tailscale serve --bg --set-path /code http://127.0.0.1:$VSC_PORT
fi
