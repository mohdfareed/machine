#!/usr/bin/env zsh

# ZINIT (zsh plugin manager)
# =============================================================================
# examples: https://zdharma-continuum.github.io/zinit/wiki/GALLERY

# set up zinit
repo="https://github.com/zdharma-continuum/zinit.git"
[ ! -d "$ZINIT_HOME" ] && mkdir -p "$(dirname "$ZINIT_HOME")"
[ ! -d "$ZINIT_HOME/.git" ] && git clone "$repo" "$ZINIT_HOME"
# shellcheck source=/dev/null
source "$ZINIT_HOME/zinit.zsh"
unset repo

# plugins
zinit light zdharma-continuum/zinit-annex-as-monitor # remote file updater
zinit light zdharma-continuum/zinit-annex-patch-dl # download with dl"URL file"

# syntax highlighting, autosuggestions, completions
zinit wait lucid light-mode for \
  atinit"zicompinit; zicdreplay; compdef _dotnet_zsh_complete dotnet" \
      zdharma-continuum/fast-syntax-highlighting \
  atload"_zsh_autosuggest_start" \
      zsh-users/zsh-autosuggestions \
  blockf atpull'zinit creinstall -q .' \
      zsh-users/zsh-completions
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}' \
'r:|[._-]=* r:|=* l:|=*' # case-insensitive completion, ignore dots and hyphens

# fzf (fuzzy finder)
zinit ice wait lucid as"program" from"gh-r" mv"fzf* -> fzf" pick"fzf" \
      atload"eval \"\$(fzf --zsh)\"" # key bindings for fzf (ctrl-t, ctrl-r)
zinit light junegunn/fzf

# fzf tab completion
zinit ice wait lucid
zinit light Aloxaf/fzf-tab

# completions style
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
