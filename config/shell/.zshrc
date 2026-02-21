#!/usr/bin/env zsh

# Environment
# =============================================================================

# homebrew
if [[ -f "/opt/homebrew/bin/brew" ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi # arm macos
if [[ -f "/usr/local/bin/brew" ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
fi # intel macos
if [[ -f "/home/linuxbrew/.linuxbrew/bin/brew" ]]; then
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
fi # linux/wsl (arm64 or x86_64)

# python
if command -v brew &>/dev/null; then
  python=$(brew --prefix python)/libexec/bin
  export PATH="$python:$PATH"
  unset python

  # python free-threading (thread-safe)
  pythont="$(brew --prefix python-freethreading)/bin"
  export PATH="$pythont:$PATH"
  unset pythont
fi

# oh-my-posh theme
theme="$(oh-my-posh cache path)/themes/pure.omp.json"
eval "$(oh-my-posh init zsh --config "$theme")"
unset theme

# Completions
# =============================================================================

# homebrew completions
if command -v brew &>/dev/null; then
  FPATH="$(brew --prefix)/share/zsh/site-functions:${FPATH}"
fi

# docker completions
FPATH="$HOME/.local/docker/completions:${FPATH}" # docker
# python (typer) apps completions
fpath+=~/.zfunc; autoload -Uz compinit; compinit
# openclaw completions
source $HOME/.openclaw/completions/openclaw.zsh

# dotnet completions, source:
# https://learn.microsoft.com/en-us/dotnet/core/tools/enable-tab-autocomplete
_dotnet_zsh_complete() {
  if [[ ! $(command -v dotnet) ]]; then
      return
  fi

  # shellcheck disable=SC2154
  local completions=("$(dotnet complete "$words")")
  # shellcheck disable=SC2128
  if [ -z "$completions" ]; then
      _arguments '*::arguments: _normal'
      return
  fi

  # this is not variable assignment, do not modify!
  # shellcheck disable=SC2283,SC2296
  _values = "${(ps:\n:)completions}"
}
compdef _dotnet_zsh_complete dotnet

# Configuration
# =============================================================================

# history
setopt appendhistory
setopt sharehistory
setopt hist_ignore_space
setopt hist_ignore_all_dups
setopt hist_save_no_dups
setopt hist_ignore_dups
setopt hist_find_no_dups

# completions style (case-insensitive, ignore dots/hyphens)
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}' 'r:|[._-]=* r:|=* l:|=*'
zstyle ':completion:*:git-checkout:*' sort false
zstyle ':completion:*:descriptions' format '[%d]'
# shellcheck disable=SC2086,SC2296
zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS}
zstyle ':completion:*' menu no
# shellcheck disable=SC2016
zstyle ':fzf-tab:complete:cd:*' fzf-preview 'eza -1 --color=always $realpath'
zstyle ':fzf-tab:*' switch-group '<' '>'
zstyle ':fzf-tab:*' fzf-command ftb-tmux-popup
# source: https://github.com/Aloxaf/fzf-tab?tab=readme-ov-file#configure

# ZINIT (zsh plugin manager)
# =============================================================================
# examples: https://zdharma-continuum.github.io/zinit/wiki/GALLERY

# set up zinit
ZINIT_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}/zinit/zinit.git"
[ ! -d $ZINIT_HOME ] && mkdir -p "$(dirname $ZINIT_HOME)"
[ ! -d $ZINIT_HOME/.git ] && git clone https://github.com/zdharma-continuum/zinit.git "$ZINIT_HOME"
source "${ZINIT_HOME}/zinit.zsh"

# fzf (before fzf-tab)
eval "$(fzf --zsh)"

# plugins (turbo — deferred to first idle prompt)
# source: https://github.com/zdharma-continuum/fast-syntax-highlighting
zinit wait lucid for \
  atinit"zicompinit; zicdreplay" zdharma-continuum/fast-syntax-highlighting \
  blockf zsh-users/zsh-completions \
  atload"!_zsh_autosuggest_start" zsh-users/zsh-autosuggestions \
  Aloxaf/fzf-tab

# Infrastructure
# =============================================================================

# functions and aliases
[[ -f "$HOME/.aliases" ]] && source "$HOME/.aliases"
# machine-specific extras
[[ -f "$HOME/.zshrc.local" ]] && source "$HOME/.zshrc.local"
