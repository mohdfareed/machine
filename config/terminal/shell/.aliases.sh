#!/usr/bin/env zsh

# =============================================================================
# MARK: Files and directories
# =============================================================================

alias cat='bat --paging=never'

if [[ "$OSTYPE" == linux* ]]; then
    # show disk usage for real filesystems
    alias disk='df -h -x tmpfs -x devtmpfs -x squashfs -x overlay -x efivarfs'
fi

if [[ "$OSTYPE" == darwin* ]]; then
    # remove hidden flag from files and directories
    alias unhide='chflags nohidden'
    alias unhide-recurse='chflags -R nohidden'
fi

# =============================================================================
# MARK: Development
# =============================================================================

# activate python virtual environment
venv::activate() {
    usage="usage: $0 [venv_dir]"
    if (($# > 1)); then echo "$usage" && return 1; fi
    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        echo "$usage" && return 0
    fi
    # shellcheck source=/dev/null
    source "${1-.venv}/bin/activate"
}

# =============================================================================
# MARK: SSH and credentials
# =============================================================================

# generate random passwords and API tokens
alias gen-pass='openssl rand -base64 32'
alias gen-token='openssl rand -hex 32'

# generate an SSH key
alias ssh::gen-key='ssh-keygen -t ed25519 -C'

# register an SSH key to authorized_keys on a host
ssh::reg-key() {
    usage="usage: $0 host [key]"
    if (( $# < 1 || $# > 2 )); then echo "$usage" && return 1; fi
    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        echo "$usage" && return 0
    fi
    ssh-copy-id -i "$HOME/.ssh/${2:-personal}.pub" "$1"
}

if [[ "$OSTYPE" == darwin* ]]; then
    # fix ssh issues by re-adding keys to keychain
    function ssh::fix-keychain {
        for file in ~/.ssh/*; do
            [[ ! -f "$file" ]] && continue
            [[ $file == *.pub ]] && continue
            [[ $file == */known_hosts* ]] && continue
            [[ $file == */config ]] && continue
            ssh-add --apple-use-keychain "$file"
        done
    }
fi

# =============================================================================
# MARK: Shell and environment
# =============================================================================

if [ "$TERM_PROGRAM" = "vscode" ]; then
    alias clear='clear && clear'
fi

alias zsh::reload='exec $SHELL'

# time shell startup
zsh::time() {
    usage="usage: $0 [iterations]"
    if (($# > 1)); then echo "$usage" && return 1; fi
    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        echo "$usage" && return 0
    fi
    for _ in $(seq 1 "${1-1}"); do time $SHELL -i -c exit; done
}

# load private values into this shell on demand
mc::secrets() {
    local file="${MC_PRIVATE:?}/machine.env"
    if [[ ! -f "$file" ]]; then
        print -u2 "No secrets file: $file"
        return 1
    fi
    dotenv::load "$file"
    echo "secrets loaded"
}
