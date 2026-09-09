#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'
$managers = @($env:MC_PACKAGE_MANAGERS -split ' ' | Where-Object { $_ })

# winget
if ('winget' -in $managers) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Host "installing winget..."
        Install-PackageProvider -Name NuGet -Force -Scope CurrentUser | Out-Null
        Install-Module -Name Microsoft.WinGet.Client -Force -Repository PSGallery -Scope CurrentUser
        Repair-WinGetPackageManager
    }

    Write-Host "updating winget..."
    winget source update
    if ($LASTEXITCODE -ne 0) { throw 'winget source update failed' }
}

# scoop
if ('scoop' -in $managers) {
    if (-not (Get-Command scoop -ErrorAction SilentlyContinue)) {
        Write-Host "installing scoop..."
        Invoke-WebRequest -UseBasicParsing -Uri https://get.scoop.sh | Invoke-Expression
    }
    else {
        Write-Host "updating scoop..."
        scoop update
    }

    if (-not (Get-Command scoop -ErrorAction SilentlyContinue)) {
        throw 'Scoop installation did not make scoop available'
    }
}
