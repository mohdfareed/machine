#!/usr/bin/env bash
set -Eeuo pipefail

# Make a macOS MacBook behave like an always-on headless server.
# Tested on macOS 26 Tahoe (Apple Silicon).

AUTO_WAKE_TIME="04:00" # daily wake time for maintenance

# MARK: Power & Sleep
# =============================================================================

# Prevent sleep when the lid is closed (clamshell mode).
# Requires power adapter; machine stays awake with display closed.
echo "configuring power management..."
sudo pmset -a sleep 0           # never system-sleep
sudo pmset -a disablesleep 1    # disable sleep entirely
sudo pmset -a displaysleep 15   # display off after 15 min (saves energy)
sudo pmset -a hibernatemode 0   # no hibernation
sudo pmset -a standby 0         # no standby
sudo pmset -a autopoweroff 0    # no auto power-off

# Auto-restart after a power failure or kernel panic.
echo "enabling auto-restart on power failure..."
sudo pmset -a autorestart 1

# Wake-on-LAN (allows remote wake via magic packet).
echo "enabling wake on LAN..."
sudo pmset -a womp 1

# Prevent idle-sleep when there are active network sessions (SSH, SMB, etc.).
echo "enabling wake on network access..."
sudo pmset -a networkoversleep 1
sudo pmset -a tcpkeepalive 1

# MARK: Scheduled Tasks
# =============================================================================

# Wake machine daily for maintenance.
echo "scheduling daily wake at $AUTO_WAKE_TIME..."
sudo pmset repeat wakeorpoweron MTWRFSU "$AUTO_WAKE_TIME"

# MARK: Security
# =============================================================================

# Enable the application firewall.
echo "enabling firewall..."
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode on

# MARK: System Defaults
# =============================================================================

echo "setting server-oriented defaults..."

# Disable App Nap so background apps keep running at full speed.
defaults write NSGlobalDomain NSAppSleepDisabled -bool true

# Disable automatic macOS updates (manage manually on a server).
defaults write com.apple.SoftwareUpdate AutomaticDownload -bool false
defaults write com.apple.SoftwareUpdate AutomaticCheckEnabled -bool false
defaults write com.apple.commerce AutoUpdate -bool false

# Disable screen saver (headless, no screen).
defaults -currentHost write com.apple.screensaver idleTime -int 0

# Disable Bluetooth (headless server, no peripherals needed).
echo "disabling bluetooth..."
sudo defaults write /Library/Preferences/com.apple.Bluetooth ControllerPowerState -int 0

echo "server setup complete — reboot recommended for all changes to take effect."
