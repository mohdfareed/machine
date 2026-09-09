#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

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

# enable developer mode
Write-Host "enabling developer mode..."
Invoke-Admin {
    $developerMode = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock"
    New-Item -Path $developerMode -Force | Out-Null
    New-ItemProperty `
        -Path $developerMode `
        -Name AllowDevelopmentWithoutDevLicense `
        -Value 1 `
        -PropertyType DWord `
        -Force | Out-Null
}

# wsl
Write-Host "setting up wsl..."
$distros = @(wsl -l -q 2>$null | ForEach-Object { $_.Trim() } | Where-Object { $_ })
if ($LASTEXITCODE -ne 0 -or $distros.Count -eq 0) {
    # failed or no distros found
    Invoke-Admin { wsl --install --no-launch }
}
