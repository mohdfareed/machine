#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

# resolve hostname
$hostname = if ($env:MC_HOSTNAME)
{ $env:MC_HOSTNAME
} else
{ $env:MC_ID
}

# set hostname
if ($hostname -and $env:COMPUTERNAME -ine $hostname)
{
    Write-Host "setting hostname..."
    Rename-Computer -NewName $hostname -Force
}

# install windows features
Write-Host "enabling windows features..."
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -NoRestart
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-RemoteDesktopConnection -NoRestart
Enable-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform -NoRestart
Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -NoRestart

# wsl
Write-Host "setting up wsl..."
$distros = @(wsl -l -q 2>$null | ForEach-Object { $_.Trim() } | Where-Object { $_ })
if ($LASTEXITCODE -ne 0 -or $distros.Count -eq 0) # failed or no distors found
{
    wsl --install
}
