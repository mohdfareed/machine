#!/usr/bin/env pwsh
param([switch]$Admin)
$ErrorActionPreference = 'Stop'

if ($Admin) {
    Write-Host "installing OpenSSH..."
    $capabilityNames = @(
        'OpenSSH.Client~~~~0.0.1.0'
        'OpenSSH.Server~~~~0.0.1.0'
    )

    foreach ($name in $capabilityNames) {
        $capability = Get-WindowsCapability -Online -Name $name
        if ($capability.State -eq 'Installed') { continue }
        $result = Add-WindowsCapability -Online -Name $name
        if ($result.RestartNeeded) {
            throw 'Restart Windows, then rerun mc deploy to finish OpenSSH setup.'
        }
    }

    Get-Service -Name sshd | Set-Service -StartupType Automatic
    # Generate the default sshd_config on a fresh installation.
    Start-Service -Name sshd
    return
}

# Elevate OpenSSH installation.
# Use the native servicing host, not Microsoft Store PowerShell.
$powershell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
gsudo --direct $powershell -NoProfile -ExecutionPolicy Bypass -File $PSCommandPath -Admin
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
