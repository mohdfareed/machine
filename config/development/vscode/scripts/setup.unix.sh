#!/usr/bin/env bash
set -Eeuo pipefail

if [[ -z "${MC_ID:-}" ]]; then
    echo "MC_ID is not set; cannot set up vscode tunnel without a hostname" >&2
    exit 1
fi

echo "setting up vscode tunnel: $MC_ID"
code tunnel service install --name "$MC_ID" --accept-server-license-terms
