#!/usr/bin/env zsh

# Functions and Aliases
# =============================================================================

alias machine-setup='$MACHINE/scripts/cli.py'

if [ "$TERM_PROGRAM" = "vscode" ]; then
    alias clear='clear && clear'
fi

alias cat='bat --paging=never'
alias vim='nvim'

alias ls='eza --icons --group-directories-first --sort=Name'
alias lst='ls -T'
alias lls='ls -lhmU --git --no-user'
alias llst='lls -T'

alias zsh::reload='exec $SHELL'
alias ssh::gen-key='ssh-keygen -t ed25519 -C'

# time shell startup
zsh::time() {
    usage="usage: $0 [iterations]"
    if (($# > 1)); then echo "$usage" && return 1; fi
    for _ in $(seq 1 "${1-1}"); do time $SHELL -i -c exit; done
}

# load dotenv file as exported variables
dotenv::load() {
    usage="usage: $0 [dotenv_file]"
    if (($# > 1)); then echo "$usage" && return 1; fi

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

    key="$HOME/.ssh/${1-personal}.pub"
    if [[ ! -f "$key" ]]; then
        echo "no public key file found"
        return 1
    fi
    host=$2

    ssh-copy-id -i "$key" "$host"
}

# register an SSH key to authorized_keys on a Windows host
ssh::reg-key-win() {
    usage="usage: $0 [key_name] [user@]host"
    if (( $# < 1 || $# > 2 )); then echo "$usage" && return 1; fi

    key="$HOME/.ssh/${1-personal}.pub"
    if [[ ! -f "$key" ]]; then
        echo "no public key file found"
        return 1
    fi
    host=$2

    keys_file="\$env:ProgramData\ssh\administrators_authorized_keys"
    pwsh_cmd="Add-Content -Path $keys_file -Value '$(<"$key")'"
    # shellcheck disable=2029
    ssh "$host" "powershell -Command \"$pwsh_cmd\""
}
