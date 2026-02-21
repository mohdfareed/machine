#!/usr/bin/env bash
set -Eeuo pipefail

# set zsh as default shell
if command -v zsh &>/dev/null; then
  echo "setting default shell to zsh..."
  sudo chsh -s "$(command -v zsh)" "$USER"
fi
