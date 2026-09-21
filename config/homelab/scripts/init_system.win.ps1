#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

# Enable Windows containers and their Hyper-V isolation before installing Docker.
Write-Host "enabling container features..."
Invoke-Admin {
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
}

# Apply upgrade policy even when Docker is already installed and packages are skipped.
winget pin add --id Docker.DockerDesktop --exact --source winget --force --accept-source-agreements
if ($LASTEXITCODE -ne 0) { throw "Could not pin Docker Desktop (exit $LASTEXITCODE)" }
