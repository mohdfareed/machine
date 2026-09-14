#!/usr/bin/env zsh

# generated app completions
FPATH="$HOME/.zfunc:${FPATH}"

# =============================================================================
# MARK: Zim
# =============================================================================

# Keep existing command history when switching frameworks.
HISTFILE="$HOME/.zsh_history"
setopt EXTENDED_HISTORY HIST_EXPIRE_DUPS_FIRST
bindkey -e

# Configure the assistance modules before loading them.
ZSH_AUTOSUGGEST_MANUAL_REBIND=1
ZSH_HIGHLIGHT_HIGHLIGHTERS=(main brackets)
ZIM_HOME="${ZDOTDIR:-$HOME}/.zim"

# Rebuild Zim's startup script only when the module selection changes.
if [[ -f "$ZIM_HOME/zimfw.zsh" ]]; then
    if [[ ! "$ZIM_HOME/init.zsh" -nt "${ZDOTDIR:-$HOME}/.zimrc" ]]; then
        source "$ZIM_HOME/zimfw.zsh" init
    fi
    source "$ZIM_HOME/init.zsh"
fi
HISTSIZE=50000

# oh-my-posh theme
eval "$(oh-my-posh init zsh --config 'pure')"

# =============================================================================
# MARK: Infrastructure
# =============================================================================

# functions and aliases
[[ -f "$HOME/.aliases" ]] && source "$HOME/.aliases"
# machine-specific extras
[[ -f "$MC_MACHINE/.zshrc" ]] && source "$MC_MACHINE/.zshrc"
