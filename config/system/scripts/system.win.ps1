#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

# install windows features
Write-Host "enabling windows features..."
Invoke-Admin {
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
    # containerization
    Install-Feature -Feature 'Containers'
    # virtualization
    Install-Feature -Feature 'HypervisorPlatform'
    Install-Feature -Feature 'Microsoft-Hyper-V-All'
    # windows sandbox
    Install-Feature -Feature 'Containers-DisposableClientVM'

    if ($failed.Count) {
        throw "Failed Windows features: $($failed -join ', ')"
    }
}
