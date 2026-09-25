#!/usr/bin/env pwsh
param([switch]$Admin)
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

# ═════════════════════════════════════════════════════════════════════════════
# Initialization
# ═════════════════════════════════════════════════════════════════════════════

if ($Admin) {  # Admin version.
    # Enable Windows containers and their Hyper-V isolation before installing Docker.
    Write-Host "enabling container features..."
    $features = @('Containers', 'Microsoft-Hyper-V-All')
    foreach ($name in $features) {
        $feature = Get-WindowsOptionalFeature -Online -FeatureName $name
        if ($feature.State -eq 'Enabled') { continue }
        Enable-WindowsOptionalFeature -Online -FeatureName $name -All -NoRestart
    }

    # Keep services running while the machine is plugged in.
    Write-Host "configuring power management..."
    powercfg /change standby-timeout-ac 0
    if ($LASTEXITCODE -ne 0) { throw "Could not disable automatic sleep" }
    powercfg /change hibernate-timeout-ac 0
    if ($LASTEXITCODE -ne 0) { throw "Could not disable automatic hibernation" }
    return
}

# Elevate machine settings without changing the user who owns the WinGet pin.
$arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"", '-Admin')
$process = Start-Process -FilePath (Get-Process -Id $PID).Path -ArgumentList $arguments `
    -Verb RunAs -Wait -PassThru
if ($process.ExitCode -ne 0) { exit $process.ExitCode }

# ═════════════════════════════════════════════════════════════════════════════
# Docker
# ═════════════════════════════════════════════════════════════════════════════

# Keep Windows containers available; WinGet's default installer flags disable them.
$wingetArguments = @(
    'install',
    '--id', 'Docker.DockerDesktop',
    '--exact', '--source', 'winget', '--scope', 'machine',
    '--accept-source-agreements', '--accept-package-agreements',
    '--override', 'install --quiet --accept-license --backend=wsl-2 --always-run-service',
    '--no-upgrade'
)

winget @wingetArguments
if ($LASTEXITCODE -notin @(0, 0x8A150061)) {
    throw "Docker Desktop install failed (exit $LASTEXITCODE)"
}

# Apply upgrade policy even when Docker is already installed and packages are skipped.
winget pin add --id Docker.DockerDesktop --exact --source winget --force --accept-source-agreements
if ($LASTEXITCODE -ne 0) { throw "Could not pin Docker Desktop (exit $LASTEXITCODE)" }
