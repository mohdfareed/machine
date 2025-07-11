#!/usr/bin/env zsh

# Functions and Aliases
# =============================================================================

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
