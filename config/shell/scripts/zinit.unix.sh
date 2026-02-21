#!/usr/bin/env zsh
set -Eeo pipefail

echo "sourcing zinit..."
# shellcheck disable=SC1091
source "${ZINIT_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/zinit}/zinit.git/zinit.zsh"

echo "updating zinit..."
zinit self-update
zinit update --all
