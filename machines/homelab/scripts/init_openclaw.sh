#!/usr/bin/env bash
set -Eeuo pipefail

if ! command -v openclaw &>/dev/null; then
    echo "installing openclaw..."
    curl -fsSL https://openclaw.ai/install.sh | bash -s -- --no-onboard
fi

if ! openclaw plugins list 2>/dev/null | grep -q openclaw-mem0; then
    openclaw plugins install @mem0/openclaw-mem0 --pin
fi
