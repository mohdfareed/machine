#!/usr/bin/env bash
set -Eeuo pipefail

# Template openclaw.json with secrets for the native macOS app.
# GUI apps don't inherit shell env vars, so we resolve ${VAR}
# references into the actual config file from the environment.

src="$MC_HOME/config/openclaw/openclaw.json"
dst="$HOME/.openclaw/openclaw.json"
mkdir -p "$(dirname "$dst")"

# Resolve ${VAR} references with values from environment.
perl -pe 's/\$\{(\w+)\}/defined $ENV{$1} ? $ENV{$1} : "\${$1}"/ge' "$src" > "$dst"

chmod 600 "$dst" # contains secrets
echo "openclaw: templated → $dst"
