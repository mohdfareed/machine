#!/usr/bin/env bash
set -Eeuo pipefail

echo "setting up vscode tunnel: $MC_NAME"
code tunnel service install --name "$MC_NAME" --accept-server-license-terms
