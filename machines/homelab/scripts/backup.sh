#!/usr/bin/env bash
set -Eeuo pipefail

# Back up homelab service data to iCloud.
# Syncs ~/.homelab/*/data/ from this machine and remote servers.
# Secrets (~/. env) are NOT backed up here - they live in MC_PRIVATE.
#
# Add remote servers to the SERVERS array below.

# REVIEW: Update this list when adding new remote homelab machines.
SERVERS=(rpi)

BACKUP_ROOT="${MC_PRIVATE:-$ICLOUD/.machine}/backups"
SSH_OPTS="-o BatchMode=yes -o ConnectTimeout=10"
RSYNC_EXCLUDE=(--exclude='*.log' --exclude='__pycache__/' --exclude='*.sock' --exclude='.DS_Store')

# ─── Local ────────────────────────────────────────────────────────────────────
echo "backing up local services..."
local_dest="$BACKUP_ROOT/$(hostname -s)"

for dir in "${MC_HOMELAB_DIR:-$HOME/.homelab}"/*/data/; do
    [[ -d "$dir" ]] || continue
    svc="$(basename "$(dirname "$dir")")"
    echo "  $svc/data"

    mkdir -p "$local_dest/$svc/data"
    rsync -a --delete "${RSYNC_EXCLUDE[@]}" "$dir" "$local_dest/$svc/data/"
done

# ─── Remote ───────────────────────────────────────────────────────────────────
for host in "${SERVERS[@]}"; do
    echo "backing up $host..."
    if ! ssh "$SSH_OPTS" "$host" true 2>/dev/null; then
        echo "  unreachable, skipping"
        continue
    fi

    dest="$BACKUP_ROOT/$host"
    src_dir="${MC_HOMELAB_DIR:-$HOME/.homelab}"

    for svc in $(ssh "$SSH_OPTS" "$host" \
        "for d in ~/$src_dir/*/data; do [ -d \"\$d\" ] && basename \"\$(dirname \"\$d\")\"; done" \
        2>/dev/null); do

        echo "  $svc/data"
        mkdir -p "$dest/$svc/data"
        rsync -az --delete -e "ssh $SSH_OPTS" "${RSYNC_EXCLUDE[@]}" \
            "$host:~/$src_dir/$svc/data/" "$dest/$svc/data/"
    done
done

echo "backups complete → $BACKUP_ROOT"
# ──────────────────────────────────────────────────────────────────────────────
echo "all backups complete → $BACKUP_ROOT"
