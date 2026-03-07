#!/usr/bin/env bash
set -Eeuo pipefail

# Inject env vars into the macOS GUI domain for OpenClaw.
#
# Config files in the repo use ${VAR} placeholders. The CLI resolves
# them via the shell environment, but the macOS GUI app (launchd) has
# no login shell — shellEnv can only find vars visible to launchd.
#
# This script exports every referenced env var into the GUI domain with
# `launchctl setenv`, so OpenClaw's shellEnv feature resolves them.
# ~/.openclaw is symlinked to the repo dir by the manifest, keeping
# runtime config changes version-controlled.

# Env vars referenced in openclaw config files.
OPENCLAW_VARS=(
    GEMINI_API_KEY
    OPENAI_API_KEY
    OPENCLAW_CRON_TOKEN
    OPENCLAW_HOOKS_TOKEN
    TAILNET_NAME
    TELEGRAM_BOT_TOKEN
    TELEGRAM_USER_ID
    TELEGRAM_WEBHOOK_SECRET
)

changed=false
for var in "${OPENCLAW_VARS[@]}"; do
    val="${!var:-}"
    [[ -z "$val" ]] && { echo "warning: $var is not set"; continue; }
    current="$(launchctl getenv "$var" 2>/dev/null || true)"
    [[ "$current" == "$val" ]] && continue
    launchctl setenv "$var" "$val"
    changed=true
done

echo "openclaw: env vars synced to launchd (${#OPENCLAW_VARS[@]} vars)"

# Restart the gateway only if env vars changed, so it re-runs shellEnv.
if $changed && command -v openclaw &>/dev/null && openclaw gateway status &>/dev/null; then
    echo "openclaw: env vars changed, restarting gateway..."
    openclaw gateway restart
fi
