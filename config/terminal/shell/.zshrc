#!/usr/bin/env zsh

# =============================================================================
# MARK: Zim
# =============================================================================

# Prefer retaining unique commands.
setopt HIST_EXPIRE_DUPS_FIRST
bindkey -e

# Generated app completions.
fpath=("$HOME/.zfunc" $fpath)

# Configure Zim modules.
ZSH_AUTOSUGGEST_MANUAL_REBIND=1
ZSH_HIGHLIGHT_HIGHLIGHTERS=(main brackets)
ZIM_HOME="${ZDOTDIR:-$HOME}/.zim"

# Initialize and load Zim.
if [[ ! "$ZIM_HOME/init.zsh" -nt "${ZDOTDIR:-$HOME}/.zimrc" ]]; then
    source "$ZIM_HOME/zimfw.zsh" init
fi
source "$ZIM_HOME/init.zsh"

# oh-my-posh theme
eval "$(oh-my-posh init zsh --config 'pure')"

# =============================================================================
# MARK: Infrastructure
# =============================================================================

# Functions and aliases.
[[ -f "$HOME/.aliases" ]] && source "$HOME/.aliases"
# Machine-specific extras.
[[ -f "$MC_MACHINE/.zshrc" ]] && source "$MC_MACHINE/.zshrc"
