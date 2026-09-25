#!/usr/bin/env pwsh
param([switch]$Admin)
$ErrorActionPreference = 'Stop'

if ($Admin) {
    Write-Host "installing OpenSSH..."
    Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
    Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
    Get-Service -Name sshd | Set-Service -StartupType Automatic
    # Generate the default sshd_config on a fresh installation.
    Start-Service -Name sshd
    return
}

# Keep Scoop's launchers usable over SSH without version-directory junctions.
scoop config no_junction true
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Elevate OpenSSH installation, not the invoking user's Scoop configuration.
$arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"", '-Admin')
$process = Start-Process -FilePath (Get-Process -Id $PID).Path -ArgumentList $arguments `
    -Verb RunAs -Wait -PassThru
if ($process.ExitCode -ne 0) { exit $process.ExitCode }
