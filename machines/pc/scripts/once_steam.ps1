#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

# Clone steam-input-bridge
Set-Location "$env:DEV"
git clone "https://github.com/mohdfareed/steam-input-bridge.git"
Set-Location "steam-input-bridge"
.\Scripts\Install-App.ps1 -Local
