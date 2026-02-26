#!/usr/bin/env bash
set -Eeuo pipefail

# Template openclaw.json with secrets for the native macOS app.
# macOS GUI apps don't inherit shell env vars, so we resolve ${VAR}
# references from ~/.env into the actual config file.

set -a
# shellcheck disable=SC1091
[[ -f "$HOME/.env" ]] && source "$HOME/.env"
set +a

src="$MC_HOME/machines/$MC_ID/openclaw.json"
dst="$HOME/.openclaw/openclaw.json"

mkdir -p "$(dirname "$dst")"

# Resolve ${VAR} references with values from environment.
perl -pe 's/\$\{(\w+)\}/defined $ENV{$1} ? $ENV{$1} : "\${$1}"/ge' \
    "$src" > "$dst"

chmod 600 "$dst" # contains secrets
echo "templated openclaw.json → $dst"
