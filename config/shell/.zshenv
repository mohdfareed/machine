#!/usr/bin/env zsh

export PATH="$HOME/.local/bin:$PATH" # local binaries
export PATH="$HOME/go/bin:$PATH" # go binaries
export PATH="/snap/bin:$PATH" # snap store
export PIP_REQUIRE_VIRTUALENV=true # python

# history
export SHELL_SESSIONS_DISABLE=1
export HISTSIZE=5000
export SAVEHIST=$HISTSIZE
export HISTDUP=erase

# fix tmux + ssh issues
export TERM=xterm-256color

# private env vars
[[ -f "$HOME/.env" ]] && { set -a; source "$HOME/.env"; set +a; }
# machine-local overrides
[[ -f "$HOME/.zshenv.local" ]] && source "$HOME/.zshenv.local"
