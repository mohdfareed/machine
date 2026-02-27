#!/usr/bin/env bash
set -Eeuo pipefail

# Sync remote servers when this machine syncs.
# NOTE: Update this list when adding new remote homelab machines.
SERVERS=(rpi)

for host in "${SERVERS[@]}"; do
    echo "syncing $host..."
    ssh -o BatchMode=yes -o ConnectTimeout=10 "$host" "mc sync -s" || echo "  $host: unreachable or failed, skipping"
done
