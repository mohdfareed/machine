#!/usr/bin/env zsh
set -Eeuo pipefail

: "${MC_HOMELAB_DIR:?}"

HOMELAB_DIR="$MC_HOMELAB_DIR"
MODULE_DOCKER="$MC_HOME/config/homelab/docker"
MACHINE_DOCKER="$MC_MACHINE/docker"

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

# Link homelab service directories without replacing real paths.
mkdir -p "$HOMELAB_DIR"

link_service() {
    local svc_dir="$1"
    local name
    name="$(basename "$svc_dir")"
    local link="$HOMELAB_DIR/$name"

    # Leave existing data for a separate migration.
    if [[ -e "$link" && ! -L "$link" ]]; then
        echo "cannot replace $link; move or migrate the existing path before deploying" >&2
        return 1
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

# =============================================================================
# MARK: Deploy
# =============================================================================

deploy_services() {
    local docker_dir="$1"
    for svc_dir in "$docker_dir"/*/; do
        [[ -f "$svc_dir/compose.yaml" ]] || continue
        echo "deploying $(basename "$svc_dir")..."

        ( # subshell for env isolation
            cd "$svc_dir"
            docker compose pull --ignore-pull-failures
            docker compose up -d --build --remove-orphans
        )
    done
}

deploy_services "$MODULE_DOCKER"
deploy_services "$MACHINE_DOCKER"

echo "all services deployed."
