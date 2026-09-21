#!/usr/bin/env zsh
set -Eeuo pipefail

# Load 1Password CLI plugins if available.
plugins_file="$HOME/.config/op/plugins.sh"
if [[ -f "$plugins_file" ]]; then
  source "$plugins_file"
fi

# Initialize selected plugins when their generated aliases are missing.
if ! alias gh >/dev/null 2>&1; then
  op plugin init gh
fi
