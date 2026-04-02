#!/usr/bin/env bash
set -Eeuo pipefail

# Server maintenance tasks run during `mc update`.

# # MARK: System Maintenance
# =============================================================================

# Install pending macOS updates (security patches and critical fixes only).
echo "checking for macOS updates..."
sw_output=$(softwareupdate -l 2>&1)
if echo "$sw_output" | grep -q "Software Update found"; then
    if echo "$sw_output" | grep -q "restart"; then
        echo "updates require a restart - skipping to avoid unplanned downtime."
        echo "run 'sudo softwareupdate --install --recommended --agree-to-license' manually."
    else
        echo "installing macOS updates (no restart required)..."
        sudo softwareupdate --install --recommended --agree-to-license 2>&1 || true
    fi
else
    echo "macOS is up to date."
fi

# Flush DNS cache.
echo "flushing DNS cache..."
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder 2>/dev/null || true

# # MARK: Cleanup
# =============================================================================

echo "cleaning up system caches..."
# Clear system log archives older than 7 days.
sudo find /var/log -name "*.gz" -mtime +7 -delete 2>/dev/null || true
# Clear Homebrew cache.
brew cleanup --prune=7 2>/dev/null || true

echo "server maintenance complete."
