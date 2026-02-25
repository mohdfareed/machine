#!/usr/bin/env bash
set -Eeuo pipefail

# Deploy all homelab Docker services.

HOMELAB_DIR="${MC_HOMELAB_DIR:-$HOME/.homelab}"
MODULE_DOCKER="$MC_HOME/config/homelab/docker"
MACHINE_DOCKER="$MC_HOME/machines/$MC_ID/docker"

if ! command -v docker &>/dev/null; then
    echo "docker not found"
    exit 1
fi

# Wait for Docker daemon to be ready (Docker Desktop can be slow to start).
echo "waiting for docker daemon..."
retries=30
until docker info &>/dev/null || (( --retries == 0 )); do
    sleep 2
done
if ! docker info &>/dev/null; then
    echo "docker daemon not available"
    exit 1
fi

# Export secrets so Docker Compose can resolve ${VAR} references.
set -a
# shellcheck disable=SC1091
[[ -f "$HOME/.env" ]] && source "$HOME/.env"
set +a

# ─── Sync service directories ────────────────────────────────────────────────
# Sync repo compose files into ~/.homelab as real directories.
# Module services are deployed first, then machine-specific ones.

sync_service() {
    local svc_dir svc target
    svc_dir="$1"
    svc="$(basename "$svc_dir")"
    target="$HOMELAB_DIR/$svc"
    mkdir -p "$target"

    # Symlink compose.yaml.
    if [[ -f "$svc_dir/compose.yaml" ]]; then
        ln -sf "$svc_dir/compose.yaml" "$target/compose.yaml"
    fi

    # Symlink version-controlled files and sub-dirs.
    # Note: can't symlink the whole service dir because of runtime state (data/, logs/).
    for entry in "$svc_dir"*/; do
        [[ -e "$entry" ]] || continue
        name="$(basename "$entry")"
        ln -sfn "$entry" "$target/$name"
    done
    for entry in "$svc_dir"*; do
        [[ -f "$entry" ]] || continue
        name="$(basename "$entry")"
        [[ "$name" == "compose.yaml" ]] && continue
        ln -sf "$entry" "$target/$name"
    done
}

for svc_dir in "$MODULE_DOCKER"/*/; do
    [[ -d "$svc_dir" ]] || continue
    sync_service "$svc_dir"
done
for svc_dir in "$MACHINE_DOCKER"/*/; do
    [[ -d "$svc_dir" ]] || continue
    sync_service "$svc_dir"
done

# ─── Deploy ──────────────────────────────────────────────────────────────────

for svc_dir in "$HOMELAB_DIR"/*/; do
    [[ -f "$svc_dir/compose.yaml" ]] || continue
    echo "deploying $(basename "$svc_dir")..."

(   # preserve cwd stack
    cd "$svc_dir"
    docker compose pull --ignore-pull-failures
    docker compose up -d --remove-orphans
)
done

echo "all services deployed."
