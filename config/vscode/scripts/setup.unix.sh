#!/usr/bin/env bash
set -Eeuo pipefail

echo "setting up vscode tunnel: $MC_ID"
code tunnel service install --name "$MC_ID" --accept-server-license-terms
