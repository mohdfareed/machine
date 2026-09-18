#!/bin/sh

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Homebrew
# ═════════════════════════════════════════════════════════════════════════════

# Activate installed commands before running deployment work.
_mc_brew=$(command -v brew 2>/dev/null) || _mc_brew=
if [ -z "$_mc_brew" ]; then
    for _mc_brew in /opt/homebrew/bin/brew /usr/local/bin/brew /home/linuxbrew/.linuxbrew/bin/brew; do
        [ -x "$_mc_brew" ] && break
    done
fi

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Commands
# ═════════════════════════════════════════════════════════════════════════════

# Keep installation destinations available before their first command is installed.
_mc_go_path=${GOPATH:-"$HOME/go"}
for _mc_bin in "$HOME/.local/bin" "${GOBIN:-${_mc_go_path%%:*}/bin}" /snap/bin; do
    case ":${PATH-}:" in
        *":$_mc_bin:"*) ;;
        *) PATH="$_mc_bin${PATH:+:$PATH}" ;;
    esac
done

# Activate Homebrew using its own shell environment.
if [ -x "$_mc_brew" ]; then
    _mc_shellenv=$("$_mc_brew" shellenv sh) || return
    eval "$_mc_shellenv"
fi

export PATH
unset _mc_brew _mc_bin _mc_go_path _mc_shellenv
