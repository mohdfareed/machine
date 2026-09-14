#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

if (-not $env:GEMS_DEV) {
    throw 'GEMS_DEV is required.'
}

# Select work repositories to clone.
$repos = @(
    'https://gwr-mpe@dev.azure.com/gwr-mpe/Gems%20Machine/_git/Gems.Build'
    'https://gwr-mpe@dev.azure.com/gwr-mpe/Gems%20Machine/_git/Gems.Core'
    'https://gwr-mpe@dev.azure.com/gwr-mpe/Gems%20Machine/_git/Gems.Machine'
    # 'https://gwr-mpe@dev.azure.com/gwr-mpe/Gems%20Machine/_git/Gems.Citrine'
    # 'https://gwr-mpe@dev.azure.com/gwr-mpe/Gems%20Machine/_git/Gems.Jenkins'
    # 'https://gwr-mpe@dev.azure.com/gwr-mpe/Gems%20Machine/_git/Gems.Testing'
)

# Clone missing work repositories without changing existing checkouts.
Push-Location -LiteralPath $env:GEMS_DEV
try {
    foreach ($url in $repos) {
        $repo = ($url.TrimEnd('/') -split '/')[-1] -replace '\.git$', ''
        if (Test-Path -LiteralPath $repo -PathType Container) {
            continue
        }

        git clone $url
        if ($LASTEXITCODE -ne 0) {
            throw "git clone failed for $repo (exit $LASTEXITCODE)"
        }
    }
}
finally {
    Pop-Location
}

# existing repo setup script
# . '\\gsserver2018\GEMSProducts\GEMS Machine\Scripts\Get-Repositories.ps1'
