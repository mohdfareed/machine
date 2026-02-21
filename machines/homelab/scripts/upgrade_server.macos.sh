#!/usr/bin/env bash
set -Eeuo pipefail

# Server maintenance tasks run during `mc upgrade`.

# MARK: Verify Power Settings
# =============================================================================

echo "verifying power management settings..."
# Re-apply critical server power settings in case they were reset by an update.
sudo pmset -a sleep 0
sudo pmset -a disablesleep 1
sudo pmset -a hibernatemode 0
sudo pmset -a standby 0
sudo pmset -a autopoweroff 0
sudo pmset -a autorestart 1
sudo pmset -a womp 1
sudo pmset -a networkoversleep 1
sudo pmset -a tcpkeepalive 1

# MARK: System Maintenance
# =============================================================================

# Run macOS periodic maintenance scripts (daily, weekly, monthly).
echo "running periodic maintenance..."
sudo periodic daily weekly monthly

# Flush DNS cache.
echo "flushing DNS cache..."
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder 2>/dev/null || true

# Purge inactive memory.
echo "purging memory cache..."
sudo purge 2>/dev/null || true

# MARK: Cleanup
# =============================================================================

echo "cleaning up system caches..."
# Clear system log archives older than 7 days.
sudo find /var/log -name "*.gz" -mtime +7 -delete 2>/dev/null || true
# Clear user caches.
rm -rf ~/Library/Caches/* 2>/dev/null || true

echo "server maintenance complete."
