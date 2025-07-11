#!/usr/bin/env pwsh

# Functions and Aliases
# =============================================================================

function GenSSHKey {
    param (
        [Parameter(Mandatory = $true)][string]$KeyName,
        [Parameter(Mandatory = $true)][string]$Email,
        [Parameter(Mandatory = $true)][SecureString]$Passphrase
    )
    ssh-keygen -t ed25519 -f "$HOME/.ssh/$KeyName" -C "$Email" -N "$Passphrase"
}
