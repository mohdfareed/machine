#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

# winget
Write-Host "setting up winget..."
winget source update

# scoop
Write-Host "setting up scoop..."
if (-not (Get-Command scoop -ErrorAction SilentlyContinue)) {
    Write-Host "installing scoop..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -UseBasicParsing -Uri https://get.scoop.sh | Invoke-Expression
}
else {
    scoop update
}
