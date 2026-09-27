#!/bin/sh

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Homebrew
# ═════════════════════════════════════════════════════════════════════════════

# Activate installed commands before running deployment work.
_mc_brew=$(command -v brew 2>/dev/null) || _mc_brew=
if [ -z "$_mc_brew" ]; then
    for _mc_brew in /opt/homebrew/bin/brew /home/linuxbrew/.linuxbrew/bin/brew; do
        [ -x "$_mc_brew" ] && break
    done
fi

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Commands
# ═════════════════════════════════════════════════════════════════════════════


# Activate Homebrew using its own shell environment.
_mc_shellenv=$("$_mc_brew" shellenv sh) || return
eval "$_mc_shellenv"

export PATH="$HOME/.local/bin:$PATH"
unset _mc_brew _mc_shellenv
