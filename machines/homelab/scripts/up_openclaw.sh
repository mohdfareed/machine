#!/usr/bin/env bash
set -Eeuo pipefail

# Update OpenClaw gateway and plugins.
# Runs on both `mc apply` and `mc update`.
echo "updating openclaw..."
curl -fsSL https://openclaw.ai/install.sh | bash -s -- --no-onboard

openclaw plugins update --all
