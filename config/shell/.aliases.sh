#!/usr/bin/env zsh

# Functions and Aliases
# =============================================================================

if [ "$TERM_PROGRAM" = "vscode" ]; then
    alias clear='clear && clear'
fi

alias ls='eza --icons --group-directories-first --sort=Name'
alias lst='ls -T'
alias lls='ls -lhmU --git --no-user'
alias llst='lls -T'

alias zsh::reload='exec $SHELL'
alias ssh::gen-key='ssh-keygen -t ed25519 -C'

alias dc='docker compose'
alias cat='bat --paging=never'
alias gen-pass='openssl rand -base64 32'

# Linux: show disk usage for real filesystems
if [[ "$OSTYPE" == linux* ]]; then
    alias disk='df -h -x tmpfs -x devtmpfs -x squashfs -x overlay -x efivarfs'
fi

# macOS: re-add all ssh keys to keychain
if [[ "$OSTYPE" == darwin* ]]; then
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

# clone a git repo
git::clone() {
    usage="usage: $0 name [args...]"
    if (($# < 1)); then echo "$usage" && return 1; fi
    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        echo "$usage" && return 0
    fi
    git clone "git@github.com:mohdfareed/$1.git" "${@:2}"
}

# time shell startup
zsh::time() {
    usage="usage: $0 [iterations]"
    if (($# > 1)); then echo "$usage" && return 1; fi
    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        echo "$usage" && return 0
    fi
    for _ in $(seq 1 "${1-1}"); do time $SHELL -i -c exit; done
}

# load dotenv file as exported variables
dotenv::load() {
    usage="usage: $0 [dotenv_file]"
    if (($# > 1)); then echo "$usage" && return 1; fi
    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        echo "$usage" && return 0
    fi

    env=${1-.env}
    if [[ ! -f "$env" ]]; then
        echo "no dotenv file found"
        return 1
    fi

    # shellcheck source=/dev/null
    source "$env"
}

# activate python virtual environment
venv::activate() {
    usage="usage: $0 [venv_dir]"
    if (($# > 1)); then echo "$usage" && return 1; fi
    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        echo "$usage" && return 0
    fi

    venv=${1-.venv}
    if [[ ! -d "$venv" ]]; then
        echo "no virtual environment directory found"
        return 1
    fi

    # shellcheck source=/dev/null
    source "$venv/bin/activate"
}

# register an SSH key to authorized_keys on a host
ssh::reg-key() {
    usage="usage: $0 [key_name] [user@]host"
    if (( $# < 1 || $# > 2 )); then echo "$usage" && return 1; fi
    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        echo "$usage" && return 0
    fi

    key="$HOME/.ssh/${1-personal}.pub"
    if [[ ! -f "$key" ]]; then
        echo "no public key file found"
        return 1
    fi
    host=$2

    ssh-copy-id -i "$key" "$host"
}
