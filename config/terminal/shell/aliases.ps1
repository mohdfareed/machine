#!/usr/bin/env pwsh

# =============================================================================
# MARK: Files and directories
# =============================================================================

Set-Alias -Name cat -Value ShowFile
function ShowFile { bat --paging=never @args }

# Match Zim's exa module defaults and shortcuts.
if (-not $env:EZA_COLORS) {
    $env:EZA_COLORS = 'da=1;34:gm=1;34:Su=1;34'
}

Set-Alias -Name ls -Value ListFiles
function ListFiles { eza --group-directories-first @args }

eza --git $PSCommandPath *> $null
if ($LASTEXITCODE -eq 0) {
    # Enable Git status only when this eza build supports it.
    function ll { ListFiles -l --git @args }
}
else {
    function ll { ListFiles -l @args }
}

function l { ll -a @args }
function lr { ll -T @args }
function lx { ll -sextension @args }
function lk { ll -ssize @args }
function lt { ll -smodified @args }
function lc { ll -schanged @args }

# =============================================================================
# MARK: Development
# =============================================================================

# Activate a Python virtual environment in this shell.
function Enter-Venv {
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

# =============================================================================
# MARK: SSH and credentials
# =============================================================================

# Generate a new SSH key pair
function GenKey {
    param (
        [Switch]$Help,
        [Parameter(Mandatory = $true)][string]$KeyName,
        [Parameter(Mandatory = $true)][string]$Email,
        [Parameter(Mandatory = $true)][SecureString]$Passphrase
    )

    if ($Help) {
        Write-Host "Usage: GenKey -KeyName <key-name> -Email <email> -Passphrase <passphrase>"
        return
    }

    ssh-keygen -t ed25519 -f "$HOME/.ssh/$KeyName" -C "$Email" -N "$Passphrase"
}

# Register an SSH key to authorized_keys on a host
function RegKey {
    param (
        [Switch]$Help,
        [Parameter(Mandatory = $true)][string]$HostName,
        [Parameter(Mandatory = $true)][string]$KeyName,
        [string]$User = $env:USERNAME
    )

    if ($Help) {
        Write-Host "Usage: RegKey -HostName <host-name> -KeyName <key-name> [-User <username>]"
        return
    }

    $pubKeyPath = "$HOME/.ssh/$KeyName.pub"
    $pubKey = Get-Content -Path $pubKeyPath -Raw
    ssh "$User@$HostName" "echo '$pubKey' >> ~/.ssh/authorized_keys"
    Write-Host "Public key $pubKeyPath added to $User@${HostName}:authorized_keys"
}

# =============================================================================
# MARK: Shell and environment
# =============================================================================

if ($env:TERM_PROGRAM -eq 'vscode') {
    function Clear {
        Clear-Host; Clear-Host
    }
}

# Load private values into this shell on demand
function Import-Secrets {
    $file = Join-Path $env:MC_PRIVATE 'machine.env' -ErrorAction Stop
    if (-not (Test-Path $file)) {
        Write-Error "no secrets file found"
        return
    }

    Import-DotEnv $file
    Write-Host "secrets loaded for this shell"
}
