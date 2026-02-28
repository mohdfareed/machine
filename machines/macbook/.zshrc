#!/usr/bin/env zsh

export PATH="$DEV_BIN:$PATH" # local dev binaries

# profile a command with gnu time
function profile {
    usage="usage: $0 command [args...]"
    if (($# < 1)); then echo "$usage" && return 1; fi

    format="\
    ===Profiling Report===
    ===Real time:    %es
    ===Memory usage: %MKB
    ===File size:    $(du -sh "$(which "$1")" | cut -f1)"
    gtime -f "$format" "$@"
}
