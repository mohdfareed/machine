# region - Plugins
# =============================================================================
# examples: https://zdharma-continuum.github.io/zinit/wiki/GALLERY

# homebrew
if [[ -f "/opt/homebrew/bin/brew" ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)" # activate homebrew
    FPATH="$(brew --prefix)/share/zsh/site-functions:${FPATH}" # completions

    # python
    if [[ -d "$(brew --prefix python)" ]]; then
        export PATH="$(brew --prefix python)/libexec/bin:$PATH"
    fi

    # nvm
    export NVM_DIR="$HOME/.nvm"
    if [ -s "$(brew --prefix nvm)/nvm.sh" ]; then
        source "$(brew --prefix nvm)/nvm.sh" # load nvm
        [ -s "$(brew --prefix nvm)/etc/bash_completion.d/nvm" ] && \
        source "$(brew --prefix nvm)/etc/bash_completion.d/nvm" # completions
    fi
fi

# pyenv (python version manager)
if command -v pyenv 1>/dev/null 2>&1; then
    eval "$(pyenv init -)"
fi

# dotnet completions, source:
# https://learn.microsoft.com/en-us/dotnet/core/tools/enable-tab-autocomplete
_dotnet_zsh_complete()
{
    if [[ ! $(command -v dotnet) ]]; then
        return
    fi

    local completions=("$(dotnet complete "$words")")
    if [ -z "$completions" ]
    then
        _arguments '*::arguments: _normal'
        return
    fi

    # this is not variable assignment, do not modify!
    _values = "${(ps:\n:)completions}"
}

# endregion
# region - Shell Plugins
# =============================================================================

# oh-my-posh theme
if [[ ! $(command -v oh-my-posh) ]]; then
    curl -s https://ohmyposh.dev/install.sh | bash -s
fi
theme="$POSH_THEMES_PATH/pure.omp.json"
eval "$(oh-my-posh init zsh --config "$theme")"
unset theme

# # pure theme
# PURE_PROMPT_SYMBOL='➜' # prompt symbol
# PURE_PROMPT_VICMD_SYMBOL='»' # vi mode symbol
# PURE_CMD_MAX_EXEC_TIME=1 # show time if command takes more than 1 second
# zstyle :prompt:pure:git:stash show yes # show stash count
# zstyle :prompt:pure:git:fetch only_upstream yes # only show upstream changes
# zinit ice pick'async.zsh' src'pure.zsh'
# zinit light sindresorhus/pure

# syntax highlighting, autosuggestions, completions
zinit wait lucid light-mode for \
  atinit"zicompinit; zicdreplay; compdef _dotnet_zsh_complete dotnet;" \
      zdharma-continuum/fast-syntax-highlighting \
  atload"_zsh_autosuggest_start" \
      zsh-users/zsh-autosuggestions \
  blockf atpull'zinit creinstall -q .' \
      zsh-users/zsh-completions
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}' \
'r:|[._-]=* r:|=* l:|=*' # case-insensitive completion, ignore dots and hyphens

# fzf (fuzzy finder) tab completion
zinit ice wait lucid
zinit light Aloxaf/fzf-tab
# source: https://github.com/Aloxaf/fzf-tab?tab=readme-ov-file#configure
zstyle ':completion:*:git-checkout:*' sort false
zstyle ':completion:*:descriptions' format '[%d]'
zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS}
zstyle ':completion:*' menu no
zstyle ':fzf-tab:complete:cd:*' fzf-preview 'eza -1 --color=always $realpath'
zstyle ':fzf-tab:*' switch-group '<' '>'
zstyle ':fzf-tab:*' fzf-command ftb-tmux-popup

# fzf (fuzzy finder)
zinit ice wait lucid as"program" from"gh-r" mv"fzf* -> fzf" pick"fzf" \
      atload"eval \"\$(fzf --zsh)\"" # key bindings for fzf (ctrl-t, ctrl-r)
zinit light junegunn/fzf

# eza (enhanced ls)
zinit ice wait lucid from"gh-r" as"program" mv"eza* -> eza"
zinit light eza-community/eza

# bat pager (cat with syntax highlighting)
zinit ice wait lucid as"command" from"gh-r" mv"bat* -> bat" pick"bat/bat"
zinit light sharkdp/bat

# tmux
zinit ice wait lucid as"command" from"gh-r" mv"tmux* -> tmux" pick"tmux/tmux"
zinit light tmux/tmux

# tmux plugin manager
[ ! -d $XDG_CONFIG_HOME/tmux/plugins/tpm ] &&
git clone https://github.com/tmux-plugins/tpm $XDG_CONFIG_HOME/tmux/plugins/tpm

# nvim dependencies ===========================================================

# lazygit
zinit ice wait lucid as"program" from"gh-r" mv"lazygit* -> lazygit" \
      pick"lazygit"
zinit light jesseduffield/lazygit

# ripgrep
zinit ice wait lucid as"program" from"gh-r" mv"ripgrep* -> rg" pick"rg/rg"
zinit light BurntSushi/ripgrep

# fd
zinit ice wait lucid as"command" from"gh-r" mv"fd* -> fd" pick"fd/fd"
zinit light sharkdp/fd

# endregion
