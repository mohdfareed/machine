#!/bin/sh
set -eu

: "${MC_HOMELAB_STORAGE_DIR:?}"
: "${MC_HOMELAB_MEDIA_DIR:?}"
: "${MC_HOMELAB_CACHE_DIR:?}"

func create_directory() {
  local directory="$1"
  local parent=$(dirname "$directory")

  if [ ! -d "$parent" ]; then
      echo "Directory not found: $parent" >&2
      exit 1
  fi

  echo "Creating homelab directory: $directory"
  mkdir -p "$directory"
}

create_directory "$MC_HOMELAB_STORAGE_DIR"
create_directory "$MC_HOMELAB_MEDIA_DIR"
create_directory "$MC_HOMELAB_CACHE_DIR"
