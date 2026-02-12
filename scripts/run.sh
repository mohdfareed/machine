#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

# Use --install/-i to re-install and exit
if [[ "$1" == "--install" || "$1" == "-i" ]]; then
    shift
    uv tool install . -e --force
    exit 0
fi

# Use --build/-b to rebuild first
if [[ "$1" == "--build" || "$1" == "-b" ]]; then
    shift
    uv sync --quiet
fi

exec uv run --quiet mc "$@"
