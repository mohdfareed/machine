#!/usr/bin/env zsh
set -eu

# Update the framework and its declared modules.
ZIM_HOME="${ZDOTDIR:-$HOME}/.zim"
source "$ZIM_HOME/zimfw.zsh" upgrade
source "$ZIM_HOME/zimfw.zsh" update
