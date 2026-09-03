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

# Create the media tree and subdirectories for downloads and media.
mkdir -p \
    "$HOMELAB_MEDIA_DIR/downloads/torrents/incomplete" \
    "$HOMELAB_MEDIA_DIR/downloads/usenet/incomplete" \
    "$HOMELAB_MEDIA_DIR/downloads/usenet/complete" \
    "$HOMELAB_MEDIA_DIR/movies" \
    "$HOMELAB_MEDIA_DIR/series" \
    "$HOMELAB_MEDIA_DIR/anime"

# On macOS, create a read-only SMB share for the media tree.
if [ "$(uname -s)" = "Darwin" ]; then
    share_record=media
    current_path=$(
        /usr/sbin/sharing -l -f json |
            /usr/bin/plutil -extract "${share_record}.path" raw -o - - 2>/dev/null
    ) || current_path=

    if [ -n "$current_path" ] && [ "$current_path" != "$HOMELAB_MEDIA_DIR" ]; then
        sudo /usr/sbin/sharing -r "$share_record"
        current_path=
    fi

    if [ -n "$current_path" ]; then
        sudo /usr/sbin/sharing -e "$share_record" -S Media -s 001 -g 000 -R 1
    else
        sudo /usr/sbin/sharing -a "$HOMELAB_MEDIA_DIR" \
            -n "$share_record" \
            -S Media \
            -s 001 \
            -g 000 \
            -R 1
    fi
fi
