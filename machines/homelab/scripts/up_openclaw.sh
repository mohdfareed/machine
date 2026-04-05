#!/usr/bin/env bash
set -Eeuo pipefail

# Update OpenClaw gateway and plugins.
echo "updating openclaw plugins..."
openclaw plugins update --all
