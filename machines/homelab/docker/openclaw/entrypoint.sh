#!/bin/bash
set -e

# Restrict state dir permissions (Docker bind mount creates it as 755)
chmod 700 /home/node/.openclaw

# --- Non-gateway: just exec straight through ---
if [ "$1" != "gateway" ]; then
    exec openclaw "$@"
fi

# --- Gateway mode ---

# Start gateway in background so we can run post-start tasks
openclaw gateway &
GW_PID=$!

paired_file="/home/node/.openclaw/devices/paired.json"
paired_contents=$({ [ -f "$paired_file" ] && cat "$paired_file"; } || echo "")

# First-run only: approve this device then wait for gateway
if [ "$paired_contents" = "" ] || [ "$paired_contents" = "{}" ]; then
    # Wait for gateway to be reachable (up to 30 s)
    echo "[entrypoint] Waiting for gateway..."
    for _ in $(seq 1 30); do
        curl -sf http://127.0.0.1:18789 >/dev/null 2>&1 && break
        sleep 1
    done

    echo "[entrypoint] Approving local device..."
    openclaw devices approve 2>/dev/null || true
fi

# Hand control back to gateway process
wait "$GW_PID"
