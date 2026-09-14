#!/bin/sh

# =============================================================================
# MARK: Homebrew
# =============================================================================

# Activate installed commands before running deployment work.
_mc_brew=$(command -v brew 2>/dev/null) || _mc_brew=
if [ -z "$_mc_brew" ]; then
    for _mc_brew in /opt/homebrew/bin/brew /usr/local/bin/brew /home/linuxbrew/.linuxbrew/bin/brew; do
        [ -x "$_mc_brew" ] && break
    done
fi

if [ -x "$_mc_brew" ]; then
    # Discover the prefix without shellenv, which can create the Homebrew paths file.
    HOMEBREW_PREFIX=$("$_mc_brew" --prefix) || return
    export HOMEBREW_PREFIX
fi

# =============================================================================
# MARK: Commands
# =============================================================================

# Keep installation destinations available before their first command is installed.
_mc_go_path=${GOPATH:-"$HOME/go"}
for _mc_bin in "$HOME/.local/bin" "${GOBIN:-${_mc_go_path%%:*}/bin}" /snap/bin; do
    case ":${PATH-}:" in
        *":$_mc_bin:"*) ;;
        *) PATH="$_mc_bin${PATH:+:$PATH}" ;;
    esac
done

# Expose Homebrew commands and prefer its unversioned Python and free-threading build.
if [ -n "${HOMEBREW_PREFIX-}" ]; then
    for _mc_bin in "$HOMEBREW_PREFIX/sbin" "$HOMEBREW_PREFIX/bin" \
        "$HOMEBREW_PREFIX/opt/python/libexec/bin" "$HOMEBREW_PREFIX/opt/python-freethreading/bin"; do
        case ":${PATH-}:" in
            *":$_mc_bin:"*) ;;
            *) PATH="$_mc_bin${PATH:+:$PATH}" ;;
        esac
    done
fi

export PATH
unset _mc_brew _mc_bin _mc_go_path
