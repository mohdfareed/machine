#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

Write-Host "installing OpenSSH..."
Invoke-Admin {
    Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
    Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
    Get-Service -Name sshd | Set-Service -StartupType Automatic
    Get-Service -Name ssh-agent | Set-Service -StartupType Automatic
}

# Configure OpenSSH to use the PowerShell MSIX executable as the default shell.
# This is the new windows default distribution for PowerShell.
$powerShellPackage = Get-AppxPackage -Name Microsoft.PowerShell
if (-not $powerShellPackage) {
    throw 'PowerShell MSIX is not installed for the current user.'
}

# Use the real executable, not the app alias; rediscover its path after MSIX updates.
# NOTE: This breaks across MSIX updates. Rerun `mc deploy terminal.ssh.server` to fix.
$defaultShell = Join-Path $powerShellPackage.InstallLocation 'pwsh.exe'
if (-not (Test-Path -LiteralPath $defaultShell -PathType Leaf)) {
    throw "PowerShell executable not found: $defaultShell"
}

Write-Host "configuring OpenSSH PowerShell..."
Invoke-Admin {
    # Set the default shell for OpenSSH to PowerShell.
    # Windows default distribution is now MSIX.
    param($defaultShell)
    New-ItemProperty `
        -Path "HKLM:\SOFTWARE\OpenSSH" `
        -Name DefaultShell `
        -Value $defaultShell `
        -PropertyType String `
        -Force | Out-Null

    # Windows OpenSSH overrides authorized_keys for Administrators to a separate
    # file (administrators_authorized_keys), breaking standard pubkey auth.
    $sshdConfig = "$env:ProgramData\ssh\sshd_config"
    (Get-Content $sshdConfig) -replace '^(Match Group administrators)', '#$1' `
        -replace '^(\s*AuthorizedKeysFile __PROGRAMDATA__)', '#$1' |

    Set-Content $sshdConfig
    Restart-Service sshd
} -ArgumentList $defaultShell
