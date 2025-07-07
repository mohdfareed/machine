#!/bin/bash

echo "setting up vscode tunnel: $MACHINE_ID"
code tunnel service install --name "$MACHINE_ID" --accept-server-license-terms
echo "vscode tunnel setup completed"
