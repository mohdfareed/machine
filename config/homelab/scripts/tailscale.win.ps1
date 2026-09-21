#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

if (-not (Get-Command tailscale -ErrorAction SilentlyContinue)) {
    throw 'tailscale not found'
}

tailscale status *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host 'connecting to tailscale...'
    tailscale up
    if ($LASTEXITCODE -ne 0) {
        throw 'tailscale connection failed'
    }
}

# Keep remote access available after logout and before automatic sign-in completes.
tailscale set --unattended=true
if ($LASTEXITCODE -ne 0) { throw 'tailscale unattended setup failed' }
