#!/bin/sh
set -eu

: "${QBT_SERVER_DOMAIN:?QBT_SERVER_DOMAIN is required}"

config_path=/config/qBittorrent/config/qBittorrent.conf

python3 /configure.py "$config_path" "$QBT_SERVER_DOMAIN"

exec /usr/local/bin/qbittorrent-entrypoint.sh "$@"
