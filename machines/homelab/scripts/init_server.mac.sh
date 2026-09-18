#!/usr/bin/env zsh
set -Eeuo pipefail

# Make a Mac behave like an always-on headless server.
# Works on MacBook (clamshell), Mac Mini, Mac Studio, etc.
# Tested on macOS 26 Tahoe (Apple Silicon).

# unlock keychain for headless access
echo "unlocking login keychain..."
while true; do
  if security unlock-keychain ~/Library/Keychains/login.keychain-db; then
    break
  fi
  read -rp "try again? [Y/n] " answer
  [[ "${answer:-y}" =~ ^[Yy]$ ]] || break
done

# ═════════════════════════════════════════════════════════════════════════════
# MARK: System Defaults
# ═════════════════════════════════════════════════════════════════════════════

echo "setting homelab defaults..."
# Disable screen saver (headless, no screen).
defaults -currentHost write com.apple.screensaver idleTime -int 0

echo "homelab setup complete - reboot recommended for all changes to take effect."
