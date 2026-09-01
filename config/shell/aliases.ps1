#!/usr/bin/env pwsh

# Functions and Aliases
# =============================================================================

Set-Alias -Name lg -Value LazyGit

if ($env:TERM_PROGRAM -eq 'vscode') {
    function Clear {
        Clear-Host; Clear-Host
    }
}

# Load private values into this shell on demand
function Secrets {
    if (-not $env:MC_PRIVATE -or -not $env:MC_ID) {
        Write-Error "mc environment not configured"
        return
    }

    $file = "$env:MC_PRIVATE/env/$env:MC_ID.env"
    if (-not (Test-Path $file)) {
        Write-Error "no secrets file found"
        return
    }

    Import-DotEnv $file
    Write-Host "secrets loaded for this shell"
}

# Clone a git repo
function GitClone {
    param (
        [Switch]$Help,
        [Parameter(Mandatory = $true)][string]$RepoName,
        [string[]]$AdditionalArgs
    )

    if ($Help) {
        Write-Host "Usage: GitClone -RepoName <repo-name> [-AdditionalArgs <arg1> <arg2> ...]"
        return
    }

    git clone "git@github.com:mohdfareed/$RepoName.git" $AdditionalArgs
}

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
    if (-Not (Test-Path $pubKeyPath)) {
        Write-Error "Public key file not found: $pubKeyPath"
        return
    }

    $pubKey = Get-Content -Path $pubKeyPath -Raw
    ssh "$User@$HostName" "echo '$pubKey' >> ~/.ssh/authorized_keys"
    Write-Host "Public key $pubKeyPath added to $User@${HostName}:authorized_keys"
}
