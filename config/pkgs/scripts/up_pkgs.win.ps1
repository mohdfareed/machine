#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

if (Get-Command winget -ErrorAction SilentlyContinue)
{
    Write-Host "upgrading winget packages..."
    winget upgrade --all --accept-package-agreements --accept-source-agreements
}

if (Get-Command scoop -ErrorAction SilentlyContinue)
{
    Write-Host "upgrading scoop packages..."
    scoop update
    scoop update *
    scoop cleanup *
}
