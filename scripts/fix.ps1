#!/usr/bin/env pwsh
#Requires -Version 7.4
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

Push-Location (Join-Path $PSScriptRoot "..")
try {
    # Upgrade and install dependencies before preparing the working tree.
    Write-Host "==> Upgrading dependencies..."
    uv lock --upgrade
    Write-Host "`n==> Syncing dependencies..."
    uv sync --dev --locked

    # Fix spelling without renaming files, then format and apply lint fixes.
    Write-Host "`n==> Fixing spelling..."
    uv run --no-sync typos --write-changes --no-check-filenames
    Write-Host "`n==> Formatting and auto-fixing..."
    uv run --no-sync ruff check --fix .
    uv run --no-sync ruff format .

    # Verify the complete result with the native checks.
    Write-Host
    & "$PSScriptRoot/check.ps1"
}
finally {
    Pop-Location
}
