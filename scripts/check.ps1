#!/usr/bin/env pwsh
#Requires -Version 7.4
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

Push-Location (Join-Path $PSScriptRoot "..")
try {
    # Check the locked environment without installing or updating dependencies.
    Write-Host "==> Checking dependencies..."
    uv lock --check
    uv sync --dev --check

    # Validate Python with the current host's interpreter.
    Write-Host "`n==> Checking Python files..."
    uv run --no-sync ruff format --check .
    uv run --no-sync ruff check .
    uv run --no-sync pyright
    uv run --no-sync pytest -q

    # Check spelling and shell syntax without executing deployment scripts.
    Write-Host "`n==> Checking spelling..."
    uv run --no-sync typos

    $scripts = Get-ChildItem app, config, machines, scripts -Recurse -File
    Write-Host "`n==> Checking shell scripts..."
    $shellScripts = @($scripts.Where({ $_.Extension -eq ".sh" }).FullName)
    uv run --no-sync shellcheck --severity=error @shellScripts

    Write-Host "`n==> Checking PowerShell scripts..."
    $powerShellScripts = @($scripts.Where({ $_.Extension -in ".ps1", ".psm1" }).FullName)
    pwsh -NoProfile -File "$PSScriptRoot/check-pwsh.ps1" @powerShellScripts

    Write-Host "`n==> All checks passed!" -ForegroundColor Green
}
finally {
    Pop-Location
}
