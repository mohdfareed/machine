# Functions and Aliases
# =============================================================================

alias zsh::reload='exec $SHELL'
alias ssh::gen-key='ssh-keygen -t ed25519 -C'

alias cat='bat --paging=never'
alias vim='nvim'

alias ls='eza --icons --group-directories-first --sort=Name'
alias lst='ls -T'
alias lls='ls -lhmU --git --no-user'
alias llst='lls -T'

if [ "$TERM_PROGRAM" = "vscode" ]; then
    alias clear='clear && clear'
fi

# copy ssh key to a new machine for the current user
ssh::copy() {
    usage="usage: $0 host [user]"
    if (($# < 1 || $# > 2)); then echo $usage && return 1; fi
    ssh-copy-id ${2-$USER}@$1
}

# time shell startup
zsh::time() {
    usage="usage: $0 [iterations]"
    if (($# > 1)); then echo $usage && return 1; fi
    for i in $(seq 1 ${1-1}); do time $SHELL -i -c exit; done
}

# load dotenv file as exported variables
env::load() {
    usage="usage: $0 [dotenv]"
    if (($# > 1)); then echo $usage && return 1; fi

    env=${1-.env}
    if [[ ! -f "$env" ]]; then
        echo "No dotenv file found"
        return 1
    fi
    source $env
}

# activate python virtual environment
venv::activate() {
    usage="usage: $0 [venv_dir]"
    if (($# > 1)); then echo $usage && return 1; fi

    venv=${1-.venv}
    if [[ ! -d "$venv" ]]; then
        echo "No virtual environment directory found"
        return 1
    fi
    source "$venv/bin/activate"
}
