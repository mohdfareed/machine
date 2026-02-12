#!/usr/bin/env sh
set -e # Exit on error

# Invoke setup script
python3 "$PWD/setup.py" "$@"
