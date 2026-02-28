#!/usr/bin/env bash
set -Eeuo pipefail

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

# Symlink ~/.homelab/<service> → repo service dirs.
mkdir -p "$HOMELAB_DIR"

link_service() {
    local svc_dir="$1"
    local name
    name="$(basename "$svc_dir")"
    local link="$HOMELAB_DIR/$name"

    # Migrate runtime data from old deploy dirs.
    if [[ -d "$link" && ! -L "$link" ]]; then
        for runtime in data logs; do
            if [[ -d "$link/$runtime" && ! -d "$svc_dir/$runtime" ]]; then
                echo "migrating $name/$runtime → repo..."
                mv "$link/$runtime" "$svc_dir/$runtime"
            fi
        done
        rm -rf "$link"
    fi

    # Create or update symlink.
    if [[ -L "$link" ]]; then
        [[ "$(readlink "$link")" == "$svc_dir" ]] && return
        rm "$link"
    fi
    ln -s "$svc_dir" "$link"
}

for svc_dir in "$MODULE_DOCKER"/*/; do
    [[ -d "$svc_dir" ]] || continue
    link_service "$svc_dir"
done
for svc_dir in "$MACHINE_DOCKER"/*/; do
    [[ -d "$svc_dir" ]] || continue
    link_service "$svc_dir"
done

# ─── Deploy ─────────────────────────────────────────────────────────────────────────────

deploy_services() {
    local docker_dir="$1"
    for svc_dir in "$docker_dir"/*/; do
        [[ -f "$svc_dir/compose.yaml" ]] || continue
        echo "deploying $(basename "$svc_dir")..."
    (
        cd "$svc_dir"
        docker compose pull --ignore-pull-failures
        docker compose up -d --remove-orphans
    )
    done
}

deploy_services "$MODULE_DOCKER"
deploy_services "$MACHINE_DOCKER"

echo "all services deployed."
