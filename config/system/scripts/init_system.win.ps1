#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

# Allow the deployed PowerShell profile to load.
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force

# Enable dotfile links before file deployment.
Write-Host 'enabling developer mode...'
Invoke-Admin {
    $path = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock'
    New-Item -Path $path -Force | Out-Null
    New-ItemProperty -Path $path -Name AllowDevelopmentWithoutDevLicense `
        -PropertyType DWord -Value 1 -Force | Out-Null
}

# resolve hostname
$hostname = if ($env:MC_HOSTNAME) {
    $env:MC_HOSTNAME
}
else {
    $env:MC_ID
}

# set hostname
if ($hostname -and $env:COMPUTERNAME -ine $hostname) {
    Write-Host "setting hostname..."
    Invoke-Admin {
        param($hostname)
        Rename-Computer -NewName $hostname -Force
    } -ArgumentList $hostname
}

# wsl
Write-Host "setting up wsl..."
$distros = @(wsl -l -q 2>$null | ForEach-Object { $_.Trim() } | Where-Object { $_ })
if ($LASTEXITCODE -ne 0 -or $distros.Count -eq 0) {
    # failed or no distros found
    Invoke-Admin { wsl --install --no-launch }
}
