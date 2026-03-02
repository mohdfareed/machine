#!/usr/bin/env bash
set -Eeuo pipefail

# NOTE: Duplicates core/init_system.linux.sh shell setup.
# ghcs doesn't include the core module - only this piece is needed.
if command -v zsh &>/dev/null; then
  echo "setting default shell to zsh..."
  sudo chsh -s "$(command -v zsh)" "$USER"
fi
