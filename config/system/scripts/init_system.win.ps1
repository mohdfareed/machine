#!/usr/bin/env pwsh
param([switch]$Admin, [string]$Hostname, [switch]$InstallWsl)
$ErrorActionPreference = 'Stop'

if ($Admin) {
    # Enable dotfile links before file deployment.
    Write-Host 'enabling developer mode...'
    $path = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock'
    New-Item -Path $path -Force | Out-Null
    New-ItemProperty -Path $path -Name AllowDevelopmentWithoutDevLicense `
        -PropertyType DWord -Value 1 -Force | Out-Null

    # set hostname
    if ($Hostname -and $env:COMPUTERNAME -ine $Hostname) {
        Write-Host "setting hostname..."
        Rename-Computer -NewName $Hostname -Force
    }

    # wsl
    if ($InstallWsl) {
        wsl --install --no-launch
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    return
}

# Allow the deployed PowerShell profile to load for the invoking user.
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force

# Resolve the selected hostname and inspect this user's WSL distributions before UAC.
$Hostname = $env:MC_ID
if ($env:MC_HOSTNAME) { $Hostname = $env:MC_HOSTNAME }
Write-Host "setting up wsl..."
try {
    # Windows PowerShell 5 can turn redirected native stderr into an error record.
    $ErrorActionPreference = 'Continue'
    $distros = @(wsl -l -q 2>$null | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    $wslExitCode = $LASTEXITCODE
}
finally {
    $ErrorActionPreference = 'Stop'
}

$arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"", '-Admin')
if ($Hostname) { $arguments += @('-Hostname', "`"$Hostname`"") }
if ($wslExitCode -ne 0 -or $distros.Count -eq 0) { $arguments += '-InstallWsl' }

# Elevate only machine settings; pass public selections explicitly across UAC.
$process = Start-Process -FilePath (Get-Process -Id $PID).Path -ArgumentList $arguments `
    -Verb RunAs -Wait -PassThru
if ($process.ExitCode -ne 0) { exit $process.ExitCode }
