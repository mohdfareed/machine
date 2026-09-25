#!/usr/bin/env pwsh
param([switch]$Admin)
$ErrorActionPreference = 'Stop'

# Elevate only this script's machine settings.
if (-not $Admin) {
    $arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"", '-Admin')
    $process = Start-Process -FilePath (Get-Process -Id $PID).Path -ArgumentList $arguments `
        -Verb RunAs -Wait -PassThru
    if ($process.ExitCode -ne 0) { exit $process.ExitCode }
    return
}

# install windows features
Write-Host "enabling windows features..."
$failed = [Collections.Generic.List[string]]::new()
function Install-Feature {
    param (
        [string]$Feature
    )

    try {
        Enable-WindowsOptionalFeature -Online -NoRestart -FeatureName $Feature -ErrorAction Stop | Out-Null
    }
    catch {
        Write-Host "failed to enable ${Feature}: $($_.Exception.Message)"
        $failed.Add($Feature)
    }
}

# wsl
Install-Feature -Feature 'Microsoft-Windows-Subsystem-Linux'
Install-Feature -Feature 'VirtualMachinePlatform'
# remote desktop
Install-Feature -Feature 'Microsoft-RemoteDesktopConnection'
# virtualization
Install-Feature -Feature 'HypervisorPlatform'
# windows sandbox
Install-Feature -Feature 'Containers-DisposableClientVM'

if ($failed.Count) {
    throw "Failed Windows features: $($failed -join ', ')"
}
