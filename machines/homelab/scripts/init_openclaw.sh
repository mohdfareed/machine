#!/usr/bin/env bash
set -Eeuo pipefail

# Fix OpenClaw config file permissions.
# OpenClaw's security audit requires 600 on all config files and 700 on the
# state dir. Git doesn't track these permissions, so we set them here.

OPENCLAW_DIR="$MC_HOME/machines/homelab/docker/openclaw"

chmod 700 "$OPENCLAW_DIR/data"
chmod 600 "$OPENCLAW_DIR/openclaw.json"
find "$OPENCLAW_DIR/config" -type f -exec chmod 600 {} +
