#!/usr/bin/env bash
set -Eeuo pipefail
shopt -s nullglob

: "${MC_HOMELAB_DIR:?MC_HOMELAB_DIR must be set}"

# Configuration
# -----------------------------------------------------------------------------

# Remote hostnames must resolve through SSH. Add more hosts to this array.
REMOTE_HOSTS=(rpi)

# Output: <backup root>/<host>/<UTC timestamp>.tar.gz
# Each host keeps its own newest 14 daily archives in iCloud.
SNAPSHOTS_TO_KEEP=14
BACKUP_ROOT="${MC_PRIVATE:-$ICLOUD/.machine}/backups"
TIMESTAMP="$(date -u +%Y-%m-%dT%H%M%SZ)"

SSH_OPTIONS=(-o BatchMode=yes -o ConnectTimeout=10)
RSYNC_EXCLUDES=(
    --exclude='*.log'
    --exclude='__pycache__/'
    --exclude='*.sock'
    --exclude='.DS_Store'
)

if [[ "$BACKUP_ROOT" != /* || "$BACKUP_ROOT" == "/" ]]; then
    echo "invalid backup root: $BACKUP_ROOT" >&2
    exit 1
fi

# Temporary workspace
# -----------------------------------------------------------------------------

# Build archives outside iCloud. Only completed archives are moved into place.
staging_root="$(mktemp -d "${TMPDIR:-/tmp}/mc-backup.XXXXXX")"
trap 'rm -rf -- "$staging_root"' EXIT

# Per-host archiving and retention
# -----------------------------------------------------------------------------

# Compress one host, publish its archive, then prune only that host's history.
archive_host() {
    local host="$1"
    local source_dir="$staging_root/$host"

    if [[ ! -d "$source_dir" ]]; then
        echo "  no service data found, skipping archive"
        return
    fi

    local host_backup_dir="$BACKUP_ROOT/$host"
    local archive="$host_backup_dir/$TIMESTAMP.tar.gz"
    local staged_archive="$staging_root/$host-$TIMESTAMP.tar.gz"

    mkdir -p "$host_backup_dir"
    tar -czf "$staged_archive" -C "$source_dir" .
    mv "$staged_archive" "$archive"

    # ISO timestamps sort chronologically, so the first entries are the oldest.
    local archives=("$host_backup_dir"/20??-??-??T??????Z.tar.gz)
    local excess
    local i

    excess=$((${#archives[@]} - SNAPSHOTS_TO_KEEP))
    for ((i = 0; i < excess; i++)); do
        rm -f -- "${archives[$i]}"
    done

    echo "  archive complete → $archive"
}

# Current host
# -----------------------------------------------------------------------------

# Resolve the path here using this host's required MC_HOMELAB_DIR.
local_host="${MC_ID:-$(hostname -s)}"
local_homelab_dir="$MC_HOMELAB_DIR"

echo "backing up $local_host..."
for data_dir in "$local_homelab_dir"/*/data/; do
    [[ -d "$data_dir" ]] || continue
    service="$(basename "$(dirname "$data_dir")")"
    echo "  $service/data"
    mkdir -p "$staging_root/$local_host/$service/data"
    rsync -a "${RSYNC_EXCLUDES[@]}" \
        "$data_dir" "$staging_root/$local_host/$service/data/"
done
archive_host "$local_host"

# Remote hosts
# -----------------------------------------------------------------------------

# Collect and archive each remote host independently. If a later host cannot be
# reached, archives already completed for other hosts remain usable.
for host in "${REMOTE_HOSTS[@]}"; do
    echo "backing up $host..."

    # The single quotes are intentional: this expression runs on the remote
    # host, so its required MC_HOMELAB_DIR determines the source path.
    if ! remote_homelab_dir="$(ssh "${SSH_OPTIONS[@]}" "$host" \
        'printf "%s" "${MC_HOMELAB_DIR:?MC_HOMELAB_DIR must be set}"' 2>/dev/null)"; then
        echo "  unreachable or MC_HOMELAB_DIR is not configured, skipping"
        continue
    fi

    # Ask the remote host which services currently have a data directory.
    # NULL_GLOB prevents zsh from failing when no service directories exist;
    # other shells ignore setopt and the directory check rejects the bare glob.
    if ! remote_services="$(ssh "${SSH_OPTIONS[@]}" "$host" \
        'setopt NULL_GLOB 2>/dev/null || true
        root="${MC_HOMELAB_DIR:?MC_HOMELAB_DIR must be set}"
        for data_dir in "$root"/*/data; do
            [ -d "$data_dir" ] && basename "$(dirname "$data_dir")"
        done' 2>/dev/null)"; then
        echo "  service discovery failed, skipping"
        continue
    fi

    while IFS= read -r service; do
        [[ -n "$service" ]] || continue
        echo "  $service/data"
        mkdir -p "$staging_root/$host/$service/data"

        # rsync passes its remote path through another shell. Escape the path so
        # an MC_HOMELAB_DIR containing spaces is still treated as one argument.
        printf -v remote_source '%q' "$remote_homelab_dir/$service/data/"
        rsync -az -e "ssh -o BatchMode=yes -o ConnectTimeout=10" \
            "${RSYNC_EXCLUDES[@]}" \
            "$host:$remote_source" \
            "$staging_root/$host/$service/data/"
    done <<< "$remote_services"

    archive_host "$host"
done
