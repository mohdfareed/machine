#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

# Keep Scoop's launchers usable over SSH without version-directory junctions.
scoop config no_junction true
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "installing OpenSSH..."
Invoke-Admin {
    Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
    Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
    Get-Service -Name sshd | Set-Service -StartupType Automatic
    # Generate the default sshd_config on a fresh installation.
    Start-Service -Name sshd
}
