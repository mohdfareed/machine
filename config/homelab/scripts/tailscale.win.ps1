#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

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

Write-Host 'configuring tailscale serve (Homepage dashboard)...'
tailscale serve --bg http://127.0.0.1:3000
if ($LASTEXITCODE -ne 0) {
    throw 'tailscale serve configuration failed'
}
tailscale serve status
