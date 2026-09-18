#!/usr/bin/env zsh

# Prefer retaining unique commands.
setopt HIST_EXPIRE_DUPS_FIRST

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Configuration
# ═════════════════════════════════════════════════════════════════════════════

# Configure Zim modules.
ZIM_HOME="${ZDOTDIR:-$HOME}/.zim"
ZSH_HIGHLIGHT_HIGHLIGHTERS=(main brackets)
fpath=("$HOME/.zsh/completions" $fpath)

# Configure history-match highlighting.
HISTORY_SUBSTRING_SEARCH_HIGHLIGHT_FOUND='fg=magenta,bold'
HISTORY_SUBSTRING_SEARCH_HIGHLIGHT_NOT_FOUND='fg=red,bold'

# Zim ─────────────────────────────────────────────────────────────────────────

# Initialize and load Zim.
if [[ ! "$ZIM_HOME/init.zsh" -nt "$HOME/.zimrc" ]]; then
  source $(brew --prefix zimfw)/share/zimfw.zsh init
fi
source "$ZIM_HOME/init.zsh"

# Completions ─────────────────────────────────────────────────────────────────

# Configure fzf-tab.
export FZF_DEFAULT_OPTS='
  --height=100%
  --bind=alt-p:toggle-preview
  --preview-window=bottom:hidden
'

eval "$(batpipe)"

# Configure completion.
zstyle ':completion:*' menu no
zstyle ':completion:*:descriptions' format '[%d]'
zstyle ':fzf-tab:*' use-fzf-default-opts yes
zstyle ':fzf-tab:*' switch-group '<' '>'
zstyle ':fzf-tab:*' fzf-command ftb-tmux-popup
zstyle ':fzf-tab:complete:*' fzf-preview 'batpipe $realpath'

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Infrastructure
# ═════════════════════════════════════════════════════════════════════════════

# Functions and aliases.
[[ -f "$HOME/.aliases" ]] && source "$HOME/.aliases"
# Machine-specific extras.
[[ -f "$HOME/.zshrc.mc" ]] && source "$HOME/.zshrc.mc"
