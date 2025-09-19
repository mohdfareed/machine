#!/usr/bin/env bash

if [[ $WSL == "true" ]]; then
    echo "detected wsl environment, skipping vscode tunnel setup"
    exit 0
fi
if [[ $MACHINE_ID == "codespaces" ]]; then
    echo "detected codespaces environment, skipping vscode tunnel setup"
    exit 0
fi

echo "setting up vscode tunnel: $MACHINE_ID"
code tunnel service install --name "$MACHINE_ID" --accept-server-license-terms
