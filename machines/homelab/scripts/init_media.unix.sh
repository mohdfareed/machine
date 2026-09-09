#!/bin/sh
set -eu

: "${MC_HOMELAB_STORAGE_DIR:?}"
: "${MC_HOMELAB_MEDIA_DIR:?}"
: "${MC_HOMELAB_CACHE_DIR:?}"

create_directory() (
  directory="$1"
  parent=$(dirname "$directory")

  if [ ! -d "$parent" ]; then
    echo "Directory not found: $parent" >&2
    exit 1
  fi

  echo "Creating homelab directory: $directory"
  mkdir -p "$directory"
)

mkdir -p  "$MC_HOMELAB_STORAGE_DIR"
mkdir -p  "$MC_HOMELAB_MEDIA_DIR"
mkdir -p  "$MC_HOMELAB_CACHE_DIR"

mkdir -p  "$MC_HOMELAB_MEDIA_DIR/movies"
mkdir -p  "$MC_HOMELAB_MEDIA_DIR/series"
mkdir -p  "$MC_HOMELAB_MEDIA_DIR/anime"
mkdir -p  "$MC_HOMELAB_MEDIA_DIR/downloads"
