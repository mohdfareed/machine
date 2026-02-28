#!/usr/bin/env bash
set -Eeuo pipefail

# Fix OpenClaw Docker config permissions.
# OpenClaw's security audit requires 600 on config files and 700 on dirs.
# Git doesn't track these, so we fix them on every apply.

OPENCLAW_DIR="$MC_HOME/machines/$MC_ID/docker/openclaw"
if [[ -d "$OPENCLAW_DIR" ]]; then
    chmod 700 "$OPENCLAW_DIR"
    mkdir -p "$OPENCLAW_DIR/data"
    chmod 700 "$OPENCLAW_DIR/data"
    [[ -f "$OPENCLAW_DIR/openclaw.json" ]] && chmod 600 "$OPENCLAW_DIR/openclaw.json"
    [[ -d "$OPENCLAW_DIR/config" ]] && find "$OPENCLAW_DIR/config" -type f -exec chmod 600 {} +
    echo "openclaw: docker permissions fixed"
fi
