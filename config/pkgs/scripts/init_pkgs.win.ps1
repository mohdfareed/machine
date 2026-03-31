#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

# winget
Write-Host "setting up winget..."
winget source update

# scoop
Write-Host "setting up scoop..."
if (-not (Get-Command scoop -ErrorAction SilentlyContinue))
{
    Write-Host "installing scoop..."
    Invoke-WebRequest -UseBasicParsing -Uri https://get.scoop.sh | Invoke-Expression
} else
{
    scoop update
}
