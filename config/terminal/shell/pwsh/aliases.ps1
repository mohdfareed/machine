#!/usr/bin/env pwsh

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Files and directories
# ═════════════════════════════════════════════════════════════════════════════

# Configure cat/bat.
Set-Alias -Name cat -Value ShowFile
function ShowFile { bat --paging=never @args }

# Configure ls similar to zsh.
Set-Alias -Name ls -Value ListFiles
function ListFiles { eza --group-directories-first @args }
function ll { ListFiles -l @args }
function l { ll -a @args }
function lr { ll -T @args }

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Development
# ═════════════════════════════════════════════════════════════════════════════

# Activate a Python virtual environment in this shell.
function Enter-VirtualEnv {
    [CmdletBinding()]
    param ([string]$Path = '.venv')

    # Python uses Activate.ps1; uv uses the lowercase filename.
    $bin = if ($IsWindows) { 'Scripts' } else { 'bin' }
    $activate = Join-Path $Path $bin 'Activate.ps1'
    if (-not (Test-Path -LiteralPath $activate -PathType Leaf)) {
        $activate = Join-Path $Path $bin 'activate.ps1'
    }

    . $activate
}

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Shell and environment
# ═════════════════════════════════════════════════════════════════════════════

if ($env:TERM_PROGRAM -eq 'vscode') {
    function Clear {
        Clear-Host; Clear-Host
    }
}
