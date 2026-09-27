alias cat 'bat --paging=never'
alias ls 'eza --group-directories-first --git --icons'

alias fish::reload "exec fish"
alias fish::time "time fish --interactive --command exit"
alias fish::check "fish --no-config --no-execute"

# macOS
if test (uname) = Darwin
    # Add/remove the hidden flag on files and directories.
    alias hide-on 'chflags -h hidden'
    alias hide-off 'chflags -h nohidden'
end

# WSL
if set --query WSL_DISTRO_NAME
    # Use the Windows SSH client and agent from WSL.
    alias ssh ssh.exe
    alias ssh-add ssh-add.exe
end

# VSCode
if test "$TERM_PROGRAM" = vscode
    alias clear 'command clear; command clear'
end
