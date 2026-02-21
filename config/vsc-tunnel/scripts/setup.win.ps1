#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

if (-not $env:MC_NAME) {
    Write-Host "MC_NAME is not set; cannot set up vscode tunnel without a hostname"
    exit 1
}

Write-Output "setting up vscode tunnel: $env:MC_NAME"
code tunnel service install --name "$env:MC_NAME" --accept-server-license-terms
