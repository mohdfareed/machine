#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

$steamInputBridgePath = "$env:DEV\steam-input-bridge"
$steamInputBridgeRepo = "https://github.com/mohdfareed/steam-input-bridge.git"

if (-not (Test-Path $steamInputBridgePath)) {
    Write-Host "Cloning steam-input-bridge repository..."
    git clone $steamInputBridgeRepo $steamInputBridgePath
}

Write-Host "Installing steam-input-bridge..."
Set-Location $steamInputBridgePath
.\Scripts\Install-App.ps1 -Local
