#!/usr/bin/env bash
set -Eeuo pipefail

# set hostname
if [[ -n "${MC_NAME:-}" ]]; then
    echo "setting hostname..."
    sudo scutil --set HostName "$MC_NAME"
    sudo scutil --set LocalHostName "$MC_NAME.local"
fi

# enable Touch ID for sudo
PAM_SUDO_PATH="/etc/pam.d/sudo_local"
if ! grep -q "pam_tid.so" "$PAM_SUDO_PATH" 2>/dev/null; then
    echo "enabling touch ID for sudo..."
    sudo mkdir -p "$(dirname "$PAM_SUDO_PATH")"
    echo "auth       sufficient     pam_tid.so" | sudo tee "$PAM_SUDO_PATH" >/dev/null
fi

# enable file/screen sharing
echo "enabling file sharing..."
sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.smbd.plist
echo "enabling screen sharing..."
sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.screensharing.plist

# MARK: System Defaults
# =============================================================================

echo "setting system defaults..."
# reduce wallpaper tinting in windows
defaults write .GlobalPreferences AppleReduceDesktopTinting -bool true
# switch windows in same space
defaults write NSGlobalDomain AppleSpacesSwitchOnActivate -bool false
# double click title bar to maximize
defaults write NSGlobalDomain AppleActionOnDoubleClick -string "Fill"
# keyboard repeat rate
defaults write NSGlobalDomain KeyRepeat -int 2
# keyboard repeat delay
defaults write NSGlobalDomain InitialKeyRepeat -int 15
# keyboard navigation
defaults write NSGlobalDomain AppleKeyboardUIMode -int 2
# tap to click
defaults write com.apple.AppleMultitouchTrackpad Clicking -bool true
# drag with trackpad
defaults write com.apple.AppleMultitouchTrackpad Dragging -bool true
# auto-hide dock
defaults write com.apple.dock autohide -bool true
# hide recent apps
defaults write com.apple.dock show-recents -bool false
# minimize with scaling
defaults write com.apple.dock mineffect -string "scale"
# dock size
defaults write com.apple.dock tilesize -int 48
# enable app expose
defaults write com.apple.dock showAppExposeGestureEnabled -bool true
# rearrange spaces based on most recent use
defaults write com.apple.dock mru-spaces -bool false
