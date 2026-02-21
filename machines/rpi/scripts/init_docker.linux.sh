#!/usr/bin/env bash
set -Eeuo pipefail

# Deploy all homelab Docker services.
# Each subdirectory of ~/homelab with a compose.yaml is a service.

HOMELAB_DIR="$HOME/homelab"

if ! command -v docker &>/dev/null; then
    echo "docker not found, skipping deploy"
    exit 0
fi

# Wait for Docker daemon to be ready.
echo "waiting for docker daemon..."
retries=30
until docker info &>/dev/null || (( --retries == 0 )); do
    sleep 2
done
if ! docker info &>/dev/null; then
    echo "docker daemon not available, skipping deploy"
    exit 0
fi

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
