#!/usr/bin/env bash
set -Eeuo pipefail

# Server maintenance tasks run during `mc upgrade`.

# MARK: Verify Power Settings
# =============================================================================

echo "verifying power management settings..."
# Re-apply critical server power settings in case they were reset by an update.
source "$(dirname "$0")/_power.macos.sh"

# MARK: System Maintenance
# =============================================================================

# Install pending macOS updates (security patches, minor releases).
echo "checking for macOS updates..."
if softwareupdate -l 2>&1 | grep -q "Software Update found"; then
    echo "installing macOS updates (may require restart)..."
    sudo softwareupdate --install --all --agree-to-license 2>&1 || true
else
    echo "macOS is up to date."
fi

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
