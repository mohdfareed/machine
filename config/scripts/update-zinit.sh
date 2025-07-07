#!/usr/bin/env zsh

echo "updating zinit plugins..."

# shellcheck source=/dev/null
source "$MACHINE_SHARED/shell/zshenv"
# shellcheck source=/dev/null
source "$ZINIT_HOME/zinit.zsh"
zinit update --all

echo "zinit plugins updated successfully"
