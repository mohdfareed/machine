#!/usr/bin/env bash
set -Eeuo pipefail

# Deploy all homelab Docker services.
#
# Creates real directories at ~/homelab/<service>/ and symlinks compose.yaml
# (and config dirs) from the repo. Runtime data (./data/, logs) is written
# into the real directory — never into the git repo.

DOCKER_SRC="$MC_HOME/machines/$MC_ID/docker"
HOMELAB_DIR="$HOME/homelab"

if ! command -v docker &>/dev/null; then
    echo "docker not found, skipping deploy"
    exit 0
fi

# Wait for Docker daemon to be ready (Docker Desktop can be slow to start).
echo "waiting for docker daemon..."
retries=30
until docker info &>/dev/null || (( --retries == 0 )); do
    sleep 2
done
if ! docker info &>/dev/null; then
    echo "docker daemon not available, skipping deploy"
    exit 0
fi

# Sync repo compose files into ~/homelab as real directories.
for svc_dir in "$DOCKER_SRC"/*/; do
    [[ -d "$svc_dir" ]] || continue
    svc="$(basename "$svc_dir")"
    target="$HOMELAB_DIR/$svc"
    mkdir -p "$target"

    # Symlink compose.yaml.
    if [[ -f "$svc_dir/compose.yaml" ]]; then
        ln -sf "$svc_dir/compose.yaml" "$target/compose.yaml"
    fi

    # Symlink version-controlled subdirs (e.g. homepage/config).
    # Skip data/ — that's runtime state, kept in the real directory.
    for sub in "$svc_dir"/*/; do
        [[ -d "$sub" ]] || continue
        name="$(basename "$sub")"
        [[ "$name" == "data" ]] && continue
        ln -sfn "$sub" "$target/$name"
    done
done

# Deploy each service that has a compose.yaml.
for svc_dir in "$HOMELAB_DIR"/*/; do
    compose="$svc_dir/compose.yaml"
    [[ -f "$compose" ]] || continue
    svc="$(basename "$svc_dir")"
    echo "deploying $svc..."
    docker compose -f "$compose" pull
    docker compose -f "$compose" up -d --remove-orphans
done

echo "all services deployed."
