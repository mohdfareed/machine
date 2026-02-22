#!/usr/bin/env zsh
set -Eeo pipefail

echo "sourcing zinit..."
zinit_home="${ZINIT_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/zinit}"
# shellcheck disable=SC1091
source "$zinit_home/zinit.git/zinit.zsh" || true

echo "updating zinit..."
zinit self-update
zinit update --all
