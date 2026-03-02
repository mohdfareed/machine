#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

# set hostname
$hostname = if ($env:MC_HOSTNAME) { $env:MC_HOSTNAME } else { $env:MC_ID }
if ($hostname) {
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
wsl --install
