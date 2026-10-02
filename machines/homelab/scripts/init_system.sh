#!/bin/sh
set -eu

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Security
# ═════════════════════════════════════════════════════════════════════════════

# Enable the application firewall.
echo "enabling firewall..."
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode on

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Power & Sleep
# ═════════════════════════════════════════════════════════════════════════════

# Disable App Nap so background apps keep running at full speed.
defaults write NSGlobalDomain NSAppSleepDisabled -bool true

echo "configuring power management..."
sudo pmset -a sleep 0           # never system-sleep
sudo pmset -a disablesleep 1    # disable sleep entirely
sudo pmset -a displaysleep 15   # display off after 15 min (saves energy)
sudo pmset -a hibernatemode 0   # no hibernation (no-op on desktops)
sudo pmset -a standby 0         # no standby
sudo pmset -a autopoweroff 0    # no auto power-off

echo "enabling auto-restart on power failure..."
sudo pmset -a autorestart 1

echo "enabling wake on LAN..."
sudo pmset -a womp 1

echo "enabling wake on network access..."
sudo pmset -a networkoversleep 1
sudo pmset -a tcpkeepalive 1
