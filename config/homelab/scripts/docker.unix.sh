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

# Recursively mirror a repo directory into a deploy target.
# Creates real directories, hardlinks individual files. Hardlinks (not
# symlinks or copies) because: containers need real files (symlink targets
# don't exist inside the container), and changes made by a container must
# propagate back to the repo for committing. Existing runtime files
# (data/, logs/) that aren't in the source are left untouched.
sync_dir() {
    local src="$1" dst="$2"
    mkdir -p "$dst"

    # Recurse into subdirectories (real dirs, not symlinks).
    while IFS= read -r -d '' entry; do
        sync_dir "$entry" "$dst/$(basename "$entry")"
    done < <(find "$src" -mindepth 1 -maxdepth 1 -type d -print0)

    # Hardlink individual files (overwrites existing; same inode = same file).
    while IFS= read -r -d '' entry; do
        ln -f "$entry" "$dst/$(basename "$entry")"
    done < <(find "$src" -mindepth 1 -maxdepth 1 -type f -print0)
}

sync_service() {
    local svc_dir="$1"
    sync_dir "$svc_dir" "$HOMELAB_DIR/$(basename "$svc_dir")"
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
