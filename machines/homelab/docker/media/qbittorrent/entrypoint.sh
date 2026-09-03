#!/bin/sh
set -eu

: "${QBT_SERVER_DOMAINS:?QBT_SERVER_DOMAINS is required}"

config_path=/config/qBittorrent/config/qBittorrent.conf

python3 /configure.py "$config_path" "$QBT_SERVER_DOMAINS"

exec /usr/local/bin/qbittorrent-entrypoint.sh "$@"
