#!/usr/bin/env zsh
set -eu

# Update declared Zim modules and rebuild their startup script.
ZIM_HOME="${ZDOTDIR:-$HOME}/.zim"
source "$(brew --prefix zimfw)/share/zimfw.zsh" update
