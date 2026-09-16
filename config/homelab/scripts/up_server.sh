#!/usr/bin/env zsh
set -Eeuo pipefail

# Flush DNS cache.
echo "flushing DNS cache..."
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder 2>/dev/null || true

# Clear system log archives older than 7 days.
echo "cleaning up system caches..."
sudo find /var/log -name "*.gz" -mtime +7 -delete 2>/dev/null || true

echo "server maintenance complete."
