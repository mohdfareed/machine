#!/usr/bin/env zsh

echo "updating unix tools..."

# shellcheck source=/dev/null
source "$MACHINE_SHARED/shell/zshenv"
# shellcheck source=/dev/null
source "$ZINIT_HOME/zinit.zsh"
zinit update --all

echo "unix tools updated successfully"
