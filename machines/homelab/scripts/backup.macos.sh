#!/usr/bin/env bash
set -Eeuo pipefail

# Back up remote server data to iCloud via rsync.
# Runs on the homelab Mac. Pulls ~/homelab/*/data/ and */.env from each server.
#
# Convention: every service stores persistent data under ./data/ relative to
# its compose file. This script syncs all of them automatically.
#
# Add servers below as: backup_server <hostname>

BACKUP_ROOT="${MC_PRIVATE:-$ICLOUD/.machine}/backups"

backup_server() {
    local host="$1"
    local dest="$BACKUP_ROOT/$host"
    mkdir -p "$dest"

    echo "backing up $host..."

    # Test connectivity (Tailscale SSH, no password).
    if ! ssh -o ConnectTimeout=10 "$host" true 2>/dev/null; then
        echo "  $host unreachable, skipping"
        return
    fi

    # Sync each service's data/ directory and .env file.
    services="$(ssh "$host" "ls -d ~/homelab/*/" 2>/dev/null)"
    for svc in $(echo "$services" | xargs -n1 basename); do

        # Sync data/ if it exists.
        if ssh "$host" "test -d ~/homelab/$svc/data" 2>/dev/null; then
            echo "  syncing $svc/data..."
            mkdir -p "$dest/$svc/data"
            rsync -az --delete \
                --exclude='*.log' \
                --exclude='__pycache__/' \
                "$host:~/homelab/$svc/data/" "$dest/$svc/data/"
        fi

        # Sync .env if it exists.
        if ssh "$host" "test -f ~/homelab/$svc/.env" 2>/dev/null; then
            echo "  syncing $svc/.env..."
            mkdir -p "$dest/$svc"
            rsync -az "$host:~/homelab/$svc/.env" "$dest/$svc/.env"
        fi
    done

    echo "  $host backup complete."
}

# ─── Local (this machine) ─────────────────────────────────────────────────────
echo "backing up local services..."
LOCAL_DEST="$BACKUP_ROOT/$(hostname -s)"
for svc_dir in "$HOME/homelab"/*/; do
    [[ -d "$svc_dir" ]] || continue
    svc="$(basename "$svc_dir")"
    if [[ -d "$svc_dir/data" ]]; then
        echo "  syncing $svc/data..."
        mkdir -p "$LOCAL_DEST/$svc/data"
        rsync -a --delete \
            --exclude='*.log' \
            --exclude='__pycache__/' \
            "$svc_dir/data/" "$LOCAL_DEST/$svc/data/"
    fi
    if [[ -f "$svc_dir/.env" ]]; then
        echo "  syncing $svc/.env..."
        mkdir -p "$LOCAL_DEST/$svc"
        cp "$svc_dir/.env" "$LOCAL_DEST/$svc/.env"
    fi
done

# ─── Remote Servers ───────────────────────────────────────────────────────────
backup_server rpi
# backup_server <next-server>
# ──────────────────────────────────────────────────────────────────────────────

echo "all backups complete → $BACKUP_ROOT"
