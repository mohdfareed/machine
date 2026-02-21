#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

# set hostname
if ($env:MC_NAME) {
    Write-Host "setting hostname..."
    Rename-Computer -NewName $env:MC_NAME -Force
}
else {
    Write-Host "MC_NAME is not set; skipping hostname configuration"
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
