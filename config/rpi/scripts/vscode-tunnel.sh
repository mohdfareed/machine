#!/bin/bash
# Set up VSCode tunnel on Linux

TUNNEL_NAME="${1:-$(hostname)}"

echo "Setting up VSCode tunnel: $TUNNEL_NAME"

# Check if code command is available
if ! command -v code &> /dev/null; then
    echo "❌ VSCode CLI not found. Please install VSCode first."
    exit 1
fi

# Set up VSCode tunnel
echo "Setting up VSCode tunnel..."
code tunnel --name "$TUNNEL_NAME" --accept-server-license-terms

echo "✓ VSCode tunnel '$TUNNEL_NAME' setup completed"
echo "You can now connect to this machine via VSCode Remote Tunnels"
