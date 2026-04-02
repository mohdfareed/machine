#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

Push-Location $env:GEMS_DEV

git clone https://gwr-mpe@dev.azure.com/gwr-mpe/Gems%20Machine/_git/Gems.Build
git clone https://gwr-mpe@dev.azure.com/gwr-mpe/Gems%20Machine/_git/Gems.Core
git clone https://gwr-mpe@dev.azure.com/gwr-mpe/Gems%20Machine/_git/Gems.Machine

# git clone https://gwr-mpe@dev.azure.com/gwr-mpe/Gems%20Machine/_git/Gems.Citrine
# git clone https://gwr-mpe@dev.azure.com/gwr-mpe/Gems%20Machine/_git/Gems.Jenkins
# git clone https://gwr-mpe@dev.azure.com/gwr-mpe/Gems%20Machine/_git/Gems.Testing

Pop-Location

# existing repo setup script
# . '\\gsserver2018\GEMSProducts\GEMS Machine\Scripts\Get-Repositories.ps1'
