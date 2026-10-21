#!/usr/bin/env bash
set -Eeuo pipefail

# Deep storage cleanup tasks run during `mc update`.

echo "running deep storage cleanup..."

# # MARK: Package Manager Cleanup
# =============================================================================

if command -v apt &>/dev/null; then
    echo "cleaning apt caches..."
    sudo apt autoremove -y
    sudo apt autoclean -y
    sudo apt clean
fi

if command -v snap &>/dev/null; then
    echo "removing old snap revisions..."
    snap list --all | awk '/disabled/{print $1, $3}' | while read -r name rev; do
        sudo snap remove "$name" --revision="$rev" 2>/dev/null || true
    done
fi

# # MARK: Log Cleanup
# =============================================================================

echo "cleaning old logs..."
# Vacuum systemd journal to 100M.
sudo journalctl --vacuum-size=100M 2>/dev/null || true
# Remove archived logs older than 7 days.
sudo find /var/log -name "*.gz" -mtime +7 -delete 2>/dev/null || true
sudo find /var/log -name "*.old" -mtime +7 -delete 2>/dev/null || true
sudo find /var/log -name "*.1" -mtime +7 -delete 2>/dev/null || true

# # MARK: Docker Cleanup
# =============================================================================

if command -v docker &>/dev/null; then
    echo "pruning unused docker resources..."
    docker system prune -af --volumes 2>/dev/null || true
fi

# # MARK: Temp & Cache Cleanup
# =============================================================================

echo "cleaning temp and cache files..."
# Clear user cache files older than 7 days.
find "${HOME}/.cache" -type f -mtime +7 -delete 2>/dev/null || true
# Clear /tmp files older than 7 days.
sudo find /tmp -type f -mtime +7 -delete 2>/dev/null || true

echo "deep storage cleanup complete."
