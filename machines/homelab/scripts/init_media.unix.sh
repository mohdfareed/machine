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

# Create the media tree and subdirectories for downloads and media.
mkdir -p \
    "$MC_HOMELAB_MEDIA_DIR/downloads/incomplete" \
    "$MC_HOMELAB_MEDIA_DIR/downloads/complete" \
    "$MC_HOMELAB_MEDIA_DIR/downloads/complete/movies" \
    "$MC_HOMELAB_MEDIA_DIR/downloads/complete/tv" \
    "$MC_HOMELAB_MEDIA_DIR/movies" \
    "$MC_HOMELAB_MEDIA_DIR/series"

# On macOS, create a read-only SMB share for the media tree.
if [ "$(uname -s)" = "Darwin" ]; then
    share_name=Media
    share_record=
    current_path=

    # The record name and SMB-visible name are separate and may differ by case.
    for candidate in "$share_name" media; do
        current_path=$(
            /usr/sbin/sharing -l -f json |
                /usr/bin/plutil -extract "${candidate}.path" raw -o - - 2>/dev/null
        ) || current_path=
        if [ -n "$current_path" ]; then
            share_record=$candidate
            break
        fi
    done

    # If the share exists but points to a different path, remove it.
    if [ -n "$current_path" ] && [ "$current_path" != "$MC_HOMELAB_MEDIA_DIR" ]; then
        sudo /usr/sbin/sharing -r "$share_record"
        share_record=
        current_path=
    fi

    if [ -z "$share_record" ]; then
        sudo /usr/sbin/sharing -a "$MC_HOMELAB_MEDIA_DIR" \
            -n "$share_name" \
            -S "$share_name" \
            -s 001 \
            -g 000 \
            -R 1
    fi
fi
