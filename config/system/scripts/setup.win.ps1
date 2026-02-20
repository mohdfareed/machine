#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

# set hostname
if ($env:MC_ID) {
    Write-Host "setting hostname..."
    Rename-Computer -NewName $env:MC_ID -Force
} else {
    Write-Host "MC_ID is not set; skipping hostname configuration"
}

# install windows features
Write-Host "enabling windows features..."
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-RemoteDesktopConnection
Enable-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform
Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform
Enable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol

# wsl
Write-Host "setting up wsl..."
wsl --install

# winget
Write-Host "setting up winget..."
winget source update

# scoop
Write-Host "setting up scoop..."
if (-not (Get-Command scoop -ErrorAction SilentlyContinue)) {
    Write-Host "installing scoop..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -UseBasicParsing -Uri https://get.scoop.sh | Invoke-Expression
}
else {
    scoop update
}
