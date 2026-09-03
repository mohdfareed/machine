#!/bin/sh
set -eu

if [ -z "${HOMELAB_MEDIA_DIR:-}" ]; then
    echo "HOMELAB_MEDIA_DIR is required" >&2
    exit 1
fi

# Do not create a fake volume directory on the internal disk when a drive is absent.
case "$HOMELAB_MEDIA_DIR" in
    /Volumes/*)
        volume_name=${HOMELAB_MEDIA_DIR#/Volumes/}
        volume_name=${volume_name%%/*}
        if [ ! -d "/Volumes/$volume_name" ]; then
            echo "Media volume is not mounted: /Volumes/$volume_name" >&2
            exit 1
        fi
        ;;
esac

mkdir -p \
    "$HOMELAB_MEDIA_DIR/downloads/torrents/incomplete" \
    "$HOMELAB_MEDIA_DIR/downloads/usenet/incomplete" \
    "$HOMELAB_MEDIA_DIR/downloads/usenet/complete" \
    "$HOMELAB_MEDIA_DIR/movies" \
    "$HOMELAB_MEDIA_DIR/series" \
    "$HOMELAB_MEDIA_DIR/anime" \
    "$HOMELAB_MEDIA_DIR/transcode"
