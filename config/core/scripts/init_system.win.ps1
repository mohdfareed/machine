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
try
{
    Enable-WindowsOptionalFeature -Online -NoRestart -FeatureName Microsoft-Windows-Subsystem-Linux
    Enable-WindowsOptionalFeature -Online -NoRestart -FeatureName Microsoft-RemoteDesktopConnection
    Enable-WindowsOptionalFeature -Online -NoRestart -FeatureName HypervisorPlatform
    Enable-WindowsOptionalFeature -Online -NoRestart -FeatureName VirtualMachinePlatform
    Enable-WindowsOptionalFeature -Online -NoRestart -FeatureName Microsoft-Hyper-V-All
    Enable-WindowsOptionalFeature -Online -NoRestart -FeatureName Containers
    Enable-WindowsOptionalFeature -Online -NoRestart -FeatureName Containers-DisposableClientVM
} catch
{
    Write-Warning "Failed to enable optional windows features, enable them manually: $_"
}

# wsl
Write-Host "setting up wsl..."
$distros = @(wsl -l -q 2>$null | ForEach-Object { $_.Trim() } | Where-Object { $_ })
if ($LASTEXITCODE -ne 0 -or $distros.Count -eq 0) # failed or no distors found
{
    wsl --install --no-launch
}
