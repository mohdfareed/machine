# =============================================================================
# MARK: Files and directories
# =============================================================================

alias cat 'bat --paging=never'
alias ls 'eza --group-directories-first'

# Keep the eza commands shared with PowerShell.
alias ll 'ls -l --git'
alias l 'll -a'
alias lr 'll -T'

# macOS
if test (uname) = Darwin
    # Add/remove the hidden flag on files and directories.
    alias hide-on 'chflags hidden'
    alias hide-on-tree 'chflags -R hidden'
    alias hide-off 'chflags nohidden'
    alias hide-off-tree 'chflags -R nohidden'
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
    if set --query _flag_help
        echo 'usage: venv::activate [venv_dir]'
        return
    end

    set --local directory .venv
    set --query argv[1]; and set directory "$argv[1]"
    source "$directory/bin/activate.fish"
end

# =============================================================================
# MARK: Shell and environment
# =============================================================================

if test "$TERM_PROGRAM" = vscode
    alias clear 'command clear; command clear'
end

alias fish::reload 'exec fish'
alias fish::check 'fish --no-config --no-execute'

# Time shell startup.
function fish::time -d 'Time Fish startup'
    argparse --max-args=1 h/help -- $argv; or return
    if set --query _flag_help
        echo 'usage: fish::time [iterations]'
        return
    end

    set --local iterations 1
    set --query argv[1]; and set iterations "$argv[1]"
    for iteration in (seq "$iterations")
        time fish --interactive --command exit
    end
end
