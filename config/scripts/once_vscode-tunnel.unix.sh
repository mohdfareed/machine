#!/usr/bin/env bash
set -Eeuo pipefail

if [[ ${WSL:-} == "true" ]]; then
    echo "detected wsl environment, skipping vscode tunnel setup"
    exit 0
fi
if [[ ${CODESPACES:-} == "true" ]]; then
    echo "detected codespaces environment, skipping vscode tunnel setup"
    exit 0
fi
if [[ -z ${MACHINE_ID:-} ]]; then
    echo "MACHINE_ID is not set; skipping vscode tunnel setup" >&2
    exit 0
fi

echo "setting up vscode tunnel: $MACHINE_ID"
code tunnel service install --name "$MACHINE_ID" --accept-server-license-terms
