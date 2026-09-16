#!/usr/bin/env zsh
set -Eeuo pipefail

# Install pending macOS updates (security patches and critical fixes only).
echo "checking for macOS updates..."
sw_output=$(softwareupdate -l 2>&1)
if echo "$sw_output" | grep -q "Software Update found"; then
  if echo "$sw_output" | grep -q "restart"; then
    echo "updates require a restart - skipping to avoid unplanned downtime."
    echo "run 'sudo softwareupdate --install --recommended --agree-to-license' manually."
  else
    echo "installing macOS updates (no restart required)..."
    sudo softwareupdate --install --recommended --agree-to-license 2>&1 || true
  fi
else
  echo "macOS is up to date."
fi
