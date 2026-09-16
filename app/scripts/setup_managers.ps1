#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'
$managers = @($env:MC_PKG_MANAGERS -split ' ' | Where-Object { $_ })

# scoop
if ('scoop' -in $managers) {
    if (-not (Get-Command scoop -ErrorAction SilentlyContinue)) {
        Write-Host "installing scoop..."
        Invoke-WebRequest -UseBasicParsing -Uri https://get.scoop.sh | Invoke-Expression
    }

    if (-not (Get-Command scoop -ErrorAction SilentlyContinue)) {
        throw 'Scoop installation did not make scoop available'
    }
}
