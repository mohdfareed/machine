#!/usr/bin/env bash
set -Eeuo pipefail

# Deploy to remote servers: copy env, sync repo.
# NOTE: Update this list when adding new remote homelab machines.
SERVERS=(rpi)
SSH_OPTS="-o BatchMode=yes -o ConnectTimeout=10"

for host in "${SERVERS[@]}"; do
    echo "deploying to $host..."
    if ! ssh $SSH_OPTS "$host" true 2>/dev/null; then
        echo "  unreachable, skipping"
        continue
    fi

    # Sync repo.
    ssh $SSH_OPTS "$host" "mc sync -s" || echo "  sync failed"
done
