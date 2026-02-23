#!/usr/bin/env bash
set -Eeuo pipefail

# Make a Mac behave like an always-on headless server.
# Works on MacBook (clamshell), Mac Mini, Mac Studio, etc.
# Tested on macOS 26 Tahoe (Apple Silicon).

AUTO_WAKE_TIME="04:00:00" # daily wake time for maintenance (HH:MM:SS)

# MARK: Power & Sleep
# =============================================================================

# Prevent sleep entirely (safe on desktops; enables clamshell mode on laptops).
echo "configuring power management..."
sudo pmset -a sleep 0           # never system-sleep
sudo pmset -a disablesleep 1    # disable sleep entirely
sudo pmset -a displaysleep 15   # display off after 15 min (saves energy)
sudo pmset -a hibernatemode 0   # no hibernation (no-op on desktops)
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

# Enable automatic macOS security updates.
echo "enabling automatic updates..."
defaults write com.apple.SoftwareUpdate AutomaticCheckEnabled -bool true
defaults write com.apple.SoftwareUpdate AutomaticDownload -bool true
defaults write com.apple.SoftwareUpdate CriticalUpdateInstall -bool true
defaults write com.apple.commerce AutoUpdate -bool true

# Disable screen saver (headless, no screen).
defaults -currentHost write com.apple.screensaver idleTime -int 0

# Disable Bluetooth (headless server, no peripherals needed).
echo "disabling bluetooth..."
sudo defaults write /Library/Preferences/com.apple.Bluetooth ControllerPowerState -int 0

# MARK: Docker
# =============================================================================

# Start Docker Desktop at login.
DOCKER_APP="/Applications/Docker.app"
if [[ -d "$DOCKER_APP" ]]; then
    echo "enabling Docker auto-start..."
    osascript -e "tell application \"System Events\" to make login item at end with properties {path:\"$DOCKER_APP\", hidden:true}" 2>/dev/null || true
fi

# Disable credential helpers so SSH deployments can pull images.
# Docker Desktop sets credsStore to "desktop", which delegates to the macOS
# keychain — inaccessible from SSH sessions. Removing it falls back to
# base64-encoded creds in config.json (acceptable for a headless server).
DOCKER_CONFIG="$HOME/.docker/config.json"
if [[ -f "$DOCKER_CONFIG" ]] && python3 -c "
import json, pathlib, sys
c = json.loads(pathlib.Path('$DOCKER_CONFIG').read_text())
sys.exit(0 if c.get('credsStore') else 1)
"; then
    echo "removing docker credential store (incompatible with SSH)..."
    python3 -c "
import json, pathlib
p = pathlib.Path('$DOCKER_CONFIG')
c = json.loads(p.read_text())
c.pop('credsStore', None)
c.pop('credStore', None)
p.write_text(json.dumps(c, indent=2))
"
fi

# MARK: Scheduled Backups
# =============================================================================

# Load the hourly backup job.
PLIST="$HOME/Library/LaunchAgents/com.mc.backup.plist"
if [[ -f "$PLIST" ]]; then
    echo "loading backup schedule..."
    launchctl bootout "gui/$(id -u)/com.mc.backup" 2>/dev/null || true
    launchctl bootstrap "gui/$(id -u)" "$PLIST"
fi

echo "server setup complete — reboot recommended for all changes to take effect."
