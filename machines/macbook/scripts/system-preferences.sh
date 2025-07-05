#!/bin/bash
# Apply macOS system preferences

echo "Applying macOS system preferences..."

# Read hostname from environment or use default
HOSTNAME=${HOSTNAME:-$(scutil --get LocalHostName)}

echo "Setting hostname to: $HOSTNAME"

# Set local host name
scutil --set LocalHostName "$HOSTNAME"

# Switch windows in same space
defaults write NSGlobalDomain AppleSpacesSwitchOnActivate -bool false

# Double click title bar to maximize
defaults write NSGlobalDomain AppleActionOnDoubleClick -string "Fill"

# Keyboard repeat rate
defaults write NSGlobalDomain KeyRepeat -int 2

# Keyboard repeat delay
defaults write NSGlobalDomain InitialKeyRepeat -int 15

# Keyboard navigation
defaults write NSGlobalDomain AppleKeyboardUIMode -int 2

# Tap to click
defaults write com.apple.AppleMultitouchTrackpad Clicking -bool true

# Drag with trackpad
defaults write com.apple.AppleMultitouchTrackpad Dragging -bool true

# Auto-hide dock
defaults write com.apple.dock autohide -bool true

# Hide recent apps
defaults write com.apple.dock show-recents -bool false

# Minimize with scaling
defaults write com.apple.dock mineffect -string "scale"

# Dock size
defaults write com.apple.dock tilesize -int 48

# Enable app expose
defaults write com.apple.dock showAppExposeGestureEnabled -bool true

# Rearrange spaces based on most recent use
defaults write com.apple.dock mru-spaces -bool false

echo "✓ macOS system preferences applied successfully"
echo "Note: Some changes may require a restart to take effect"
