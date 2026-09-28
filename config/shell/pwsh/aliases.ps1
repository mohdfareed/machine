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

function search {
    <#
    .SYNOPSIS
    Search file contents with ripgrep and fzf.
    .PARAMETER Pattern
    The initial ripgrep search pattern.
    #>
    param([Parameter(Mandatory)][string]$Pattern)
    Invoke-PsFzfRipgrep -SearchString $Pattern
}

# ═════════════════════════════════════════════════════════════════════════════
# Powershell
# ═════════════════════════════════════════════════════════════════════════════

function pwsh::reload {
    . $PROFILE.CurrentUserAllHosts
}
function pwsh::time {
    $time = (Measure-Command { pwsh -Command "Exit" }).TotalMilliseconds
    Write-Host "Elapsed time: $time ms"
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
