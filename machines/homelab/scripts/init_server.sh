#!/usr/bin/env zsh
set -Eeuo pipefail

# Make a Mac behave like an always-on headless server.
# Works on MacBook (clamshell), Mac Mini, Mac Studio, etc.
# Tested on macOS 26 Tahoe (Apple Silicon).

# daily wake time for maintenance (HH:MM:SS)
AUTO_WAKE_TIME="04:00:00"

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

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Scheduled Backups
# ═════════════════════════════════════════════════════════════════════════════

# Wake machine daily for maintenance.
echo "scheduling daily wake at $AUTO_WAKE_TIME..."
sudo pmset repeat wakeorpoweron MTWRFSU "$AUTO_WAKE_TIME"

# Load the daily backup job.
PLIST="$HOME/Library/LaunchAgents/com.mc.backup.plist"
if [[ -f "$PLIST" ]]; then
  echo "loading backup schedule..."
  launchctl bootout "gui/$(id -u)/com.mc.backup" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$PLIST"
fi

echo "homelab setup complete - reboot recommended for all changes to take effect."
