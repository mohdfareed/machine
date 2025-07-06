#!/bin/bash

TUNNEL_NAME="${1:-$(hostname)}"

echo "setting up vscode tunnel: $TUNNEL_NAME"
code tunnel service install --name "$TUNNEL_NAME" --accept-server-license-terms
echo "vscode tunnel setup completed"
