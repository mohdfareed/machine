#!/usr/bin/env zsh

echo "setting up unix..."

# shellcheck source=/dev/null
source "$MACHINE_SHARED/shell/zshenv"
# shellcheck source=/dev/null
source "$ZINIT_HOME/zinit.zsh"
zinit update --all

echo "unix set up successfully"
