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

for var in "${OPENCLAW_VARS[@]}"; do
    val="${!var:-}"
    [[ -z "$val" ]] && { echo "warning: $var is not set"; continue; }
    launchctl setenv "$var" "$val"
done

echo "openclaw: env vars injected into launchd (${#OPENCLAW_VARS[@]} vars)"
