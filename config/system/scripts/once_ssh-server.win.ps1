#! /usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

# install OpenSSH server if not present
$cap = Get-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
if ($cap.State -ne 'Installed') {
    Write-Host "installing OpenSSH server..."
    Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
}

Write-Host "configuring SSH services..."
Get-Service -Name sshd | Set-Service -StartupType Automatic
Get-Service -Name ssh-agent | Set-Service -StartupType Automatic

# Windows OpenSSH overrides authorized_keys for Administrators to a separate
# file (administrators_authorized_keys), breaking standard pubkey auth.
# Comment out those lines so ~/.ssh/authorized_keys is used for all users.
$sshdConfig = "$env:ProgramData\ssh\sshd_config"
(Get-Content $sshdConfig) -replace '^(Match Group administrators)', '#$1' `
                          -replace '^(\s*AuthorizedKeysFile __PROGRAMDATA__)', '#$1' |
    Set-Content $sshdConfig

Restart-Service sshd
