#!/bin/sh
set -eu

if [ -z "${MC_HOMELAB_MEDIA_DIR:-}" ]; then
    echo "MC_HOMELAB_MEDIA_DIR is required" >&2
    exit 1
fi

# Do not create a fake volume directory on the internal disk when a drive is absent.
case "$MC_HOMELAB_MEDIA_DIR" in
    /Volumes/*)
        volume_name=${MC_HOMELAB_MEDIA_DIR#/Volumes/}
        volume_name=${volume_name%%/*}
        if [ ! -d "/Volumes/$volume_name" ]; then
            echo "Media volume is not mounted: /Volumes/$volume_name" >&2
            exit 1
        fi
        ;;
esac

# Provision the host mount point; applications own their internal directories.
mkdir -p "$MC_HOMELAB_MEDIA_DIR"
