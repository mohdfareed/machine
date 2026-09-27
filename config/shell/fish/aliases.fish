# =============================================================================
# MARK: Files and directories
# =============================================================================

alias cat 'bat --paging=never'
alias ls 'eza --group-directories-first --git --icons --color=always'

# macOS
if test (uname) = Darwin
    # Add/remove the hidden flag on files and directories.
    alias hide-on 'chflags hidden'
    alias hide-off 'chflags nohidden'
end

# =============================================================================
# MARK: SSH and credentials
# =============================================================================

# Use the Windows SSH client and agent from WSL.
if set --query WSL_DISTRO_NAME
    alias ssh ssh.exe
    alias ssh-add ssh-add.exe
end

# Generate random passwords and API tokens.
alias gen-pass 'openssl rand -base64 32'
alias gen-token 'openssl rand -hex 32'
alias gen-key 'ssh-keygen -t ed25519 -C'

# =============================================================================
# MARK: Development
# =============================================================================

# Activate a Python virtual environment in this shell.
function venv::activate -d 'Activate a Python virtual environment'
    argparse --max-args=1 h/help -- $argv; or return
    if set -q _flag_help
        echo "usage: $(status current-command) [DIR=.venv]"; return
    end

    set -l dir .venv
    set -q argv[1]; and set dir "$argv[1]"
    source "$dir/bin/activate.fish"
end

# =============================================================================
# MARK: Shell and Environment
# =============================================================================

alias fish::reload "exec fish"
alias fish::check "fish --no-config --no-execute"
alias fish::time "time fish --interactive --command exit"

if test "$TERM_PROGRAM" = vscode
    alias clear 'command clear; command clear'
end
