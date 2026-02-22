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
  export PATH="$HOMEBREW_PREFIX/opt/python/libexec/bin:$PATH"
  # python free-threading (thread-safe) — only if installed
  [[ -d "$HOMEBREW_PREFIX/opt/python-freethreading/bin" ]] \
    && export PATH="$HOMEBREW_PREFIX/opt/python-freethreading/bin:$PATH"
fi

# oh-my-posh theme
() {
  local themes
  if [[ -n "$HOMEBREW_PREFIX" ]]; then
    themes="$HOMEBREW_PREFIX/opt/oh-my-posh/themes"
  else
    themes="$(oh-my-posh cache path)/themes"
  fi
  eval "$(oh-my-posh init zsh --config "$themes/pure.omp.json")"
}

# Completions
# =============================================================================

# homebrew completions
if [[ -n "$HOMEBREW_PREFIX" ]]; then
  FPATH="$HOMEBREW_PREFIX/share/zsh/site-functions:${FPATH}"
fi

# docker completions
FPATH="$HOME/.local/docker/completions:${FPATH}"
FPATH="$HOME/.docker/completions:${FPATH}"

# python (typer) apps completions (must remain commented)
# fpath+=~/.zfunc; autoload -Uz compinit; compinit
fpath+=~/.zfunc

# dotnet completions
eval "$(dotnet completions script zsh)"

# openclaw completions
() {
  local openclaw_completions="$HOME/.openclaw/completions/openclaw.zsh"
  [[ -f "$openclaw_completions" ]] && source "$openclaw_completions"
}

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
