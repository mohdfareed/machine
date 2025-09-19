#!/usr/bin/env pwsh

# Functions and Aliases
# =============================================================================

Set-Alias machine-setup "$env:MACHINE/scripts/cli.py"

if ($env:TERM_PROGRAM -eq 'vscode') {
    function Clear {
        Clear-Host; Clear-Host
    }
}

# Generate a new SSH key pair
function GenKey {
    param (
        [Parameter(Mandatory = $true)][string]$KeyName,
        [Parameter(Mandatory = $true)][string]$Email,
        [Parameter(Mandatory = $true)][SecureString]$Passphrase
    )
    ssh-keygen -t ed25519 -f "$HOME/.ssh/$KeyName" -C "$Email" -N "$Passphrase"
}

# Register an SSH key to authorized_keys on a host
function RegKey {
    param (
        [Parameter(Mandatory = $true)][string]$HostName,
        [Parameter(Mandatory = $true)][string]$KeyName,
        [string]$User = $env:USER
    )

    $pubKeyPath = "$HOME/.ssh/$KeyName.pub"
    if (-Not (Test-Path $pubKeyPath)) {
        Write-Error "Public key file not found: $pubKeyPath"
        return
    }

    $pubKey = Get-Content -Path $pubKeyPath -Raw
    ssh "$User@$HostName" "echo '$pubKey' >> ~/.ssh/authorized_keys"
    Write-Host "Public key $pubKeyPath added to $User@${HostName}:authorized_keys"
}

# Register an SSH key to authorized_keys on a Windows host
function RegKeyWin {
    param (
        [Parameter(Mandatory = $true)][string]$HostName,
        [Parameter(Mandatory = $true)][string]$KeyName,
        [string]$User = $env:USER
    )

    $pubKeyPath = "$HOME/.ssh/$KeyName.pub"
    if (-Not (Test-Path $pubKeyPath)) {
        Write-Error "Public key file not found: $pubKeyPath"
        return
    }

    $pubKey = Get-Content -Path $pubKeyPath -Raw
    $keysFile = '$env:ProgramData\ssh\administrators_authorized_keys'
    ssh "$User@$HostName" "powershell -Command `"Add-Content -Path $keysFile -Value '$pubKey'`""
    Write-Host "Public key $pubKeyPath added to $User@${HostName}:administrators_authorized_keys"
}
