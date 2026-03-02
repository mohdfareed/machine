#!/usr/bin/env bash
set -Eeuo pipefail

# Install the OpenClaw gateway.
echo "installing openclaw..."
curl -fsSL https://openclaw.ai/install.sh | bash
