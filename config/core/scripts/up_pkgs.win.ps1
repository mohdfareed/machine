#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'
$managers = @($env:MC_PACKAGE_MANAGERS -split ' ' | Where-Object { $_ })

if ('winget' -in $managers) {
    Write-Host "upgrading winget packages..."
    winget upgrade --all --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw 'winget upgrade failed' }
}

if ('scoop' -in $managers) {
    Write-Host "upgrading scoop packages..."
    scoop update
    scoop update *
    scoop cleanup *
}
