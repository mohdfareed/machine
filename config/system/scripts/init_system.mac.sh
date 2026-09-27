#!/bin/sh
set -eu

# ═════════════════════════════════════════════════════════════════════════════
# MARK: General Settings
# ═════════════════════════════════════════════════════════════════════════════

# set hostname
target_hostname="${MC_HOSTNAME:-$MC_ID}"
if [ -n "$target_hostname" ] && [ "$(scutil --get LocalHostName)" != "$target_hostname" ]; then
    echo "setting hostname..."
    sudo scutil --set LocalHostName "$target_hostname"
fi

# enable Touch ID for sudo
PAM_SUDO_PATH="/etc/pam.d/sudo_local"
if ! grep -q "pam_tid.so" "$PAM_SUDO_PATH" 2>/dev/null; then
    echo "enabling touch ID for sudo..."
    sudo mkdir -p "$(dirname "$PAM_SUDO_PATH")"
    echo "auth       sufficient     pam_tid.so" | sudo tee "$PAM_SUDO_PATH" >/dev/null
fi

# enable hush login
[ -f "$HOME/.hushlogin" ] || touch "$HOME/.hushlogin"

echo "enabling auto-restart on power failure..."
sudo pmset -a autorestart 1

echo "enabling wake on LAN..."
sudo pmset -a womp 1

# ═════════════════════════════════════════════════════════════════════════════
# MARK: System Defaults
# ═════════════════════════════════════════════════════════════════════════════

echo "enabling auto-restart on power failure..."
sudo pmset -a autorestart 1

echo "enabling wake on LAN..."
sudo pmset -a womp 1

# Enable automatic macOS security updates.
echo "enabling automatic updates..."
defaults write com.apple.SoftwareUpdate AutomaticCheckEnabled -bool true
defaults write com.apple.SoftwareUpdate AutomaticDownload -bool true
defaults write com.apple.SoftwareUpdate CriticalUpdateInstall -bool true
defaults write com.apple.commerce AutoUpdate -bool true # Auto-update apps.

echo "setting system defaults..."

# KB/M: keyboard repeat rate
defaults write NSGlobalDomain KeyRepeat -int 2
# KB/M: keyboard repeat delay
defaults write NSGlobalDomain InitialKeyRepeat -int 15
# KB/M: trackpad double tap to click
defaults write com.apple.AppleMultitouchTrackpad Clicking -bool true
# KB/M: trackpad sticky dragging
defaults write com.apple.AppleMultitouchTrackpad Dragging -bool true

# Dock: disable rearranging spaces based on most recent use
defaults write com.apple.dock mru-spaces -bool false
# Dock: enable app expose
defaults write com.apple.dock showAppExposeGestureEnabled -bool true
# Dock: hide recent apps
defaults write com.apple.dock show-recents -bool false
# Dock: dock size
defaults write com.apple.dock tilesize -int 48
# Dock: auto-hide dock
defaults write com.apple.dock autohide -bool true

# Finder: default to list view
defaults write com.apple.finder FXPreferredViewStyle -string "Nlsv"
# Finder: sort folders first
defaults write com.apple.finder _FXSortFoldersFirst -bool true

# double click title bar to maximize
defaults write NSGlobalDomain AppleActionOnDoubleClick -string "Fill"

# time machine excluded paths
# NOTE: Requires full disk access.
sudo /usr/bin/tmutil addexclusion -p \
  "$HOME/Downloads" \
  "$HOME/Library/Cache" \
  "$HOME/Library/Developer/Xcode/DerivedData" \
  "$HOME/Library/Containers/com.docker.docker/Data/vms" || true
