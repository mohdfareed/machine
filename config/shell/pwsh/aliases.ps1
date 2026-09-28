#!/usr/bin/env pwsh

# ═════════════════════════════════════════════════════════════════════════════
# Aliases
# ═════════════════════════════════════════════════════════════════════════════

function cat { bat --color=auto --paging=never @args }
carapace bat powershell | Out-String | Invoke-Expression
Register-ArgumentCompleter -Native -CommandName cat `
    -ScriptBlock ${function:_bat_completer}

function ls { eza --color=auto --group-directories-first --git --icons=auto @args }
carapace eza powershell | Out-String | Invoke-Expression
Register-ArgumentCompleter -Native -CommandName ls `
    -ScriptBlock ${function:_eza_completer}

function ll { ls -l @args }
function lt { param([int]$Level=1) ls -TL="$Level" @args }
function llt { param([int]$Level=1) ll -TL="$Level" @args }

Set-Alias search::files Invoke-PsFzfRipgrep
Set-Alias search::proc Invoke-FuzzyKillProcess
Set-Alias search::git Invoke-FuzzyGitStatus
Set-Alias search::git::log Invoke-PsFzfGitHashes
Set-Alias search::git::branches Invoke-PsFzfGitBranches
Set-Alias search::git::tags Invoke-PsFzfGitTags
Set-Alias search::git::stashes Invoke-PsFzfGitStashes

# ═════════════════════════════════════════════════════════════════════════════
# Powershell
# ═════════════════════════════════════════════════════════════════════════════

function pwsh::time {
    $time = (Measure-Command { pwsh -Command "Exit" }).TotalMilliseconds
    Write-Host "Elapsed time: $time ms"
}
function pwsh::reload {
    if ($IsWindows) {
        & "$PSHOME/pwsh.exe" -NoLogo
        exit
    } else {
        exec "$PSHOME/pwsh" -NoLogo
    }
}

# ═════════════════════════════════════════════════════════════════════════════
# OS-Specific
# ═════════════════════════════════════════════════════════════════════════════

# macOS
if ($IsMacOS) {
    function Hide-Item {
        param([string]$Path = ".", [switch]$Recursive)
        $recurse = if ($Recursive) { '-R' }
        chflags -h $recurse hidden $Path
    }

    function Show-Item {
        param([string]$Path = ".", [switch]$Recursive)
        $recurse = if ($Recursive) { '-R' }
        chflags -h $recurse nohidden $Path
    }
}

# WSL
if ($env:WSL_DISTRO_NAME) {
    Set-Alias -Name ssh -Value ssh.exe
    Set-Alias -Name ssh-add -Value ssh-add.exe
}

# VSCode
if ($env:TERM_PROGRAM -eq 'vscode') {
    function Clear {
        Clear-Host; Clear-Host
    }
}
