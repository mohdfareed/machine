#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

if (-not $env:MC_ID)
{
    Write-Host "MC_ID is not set; cannot set up vscode tunnel without a hostname"
    exit 1
}

Write-Output "setting up vscode tunnel: $env:MC_ID"
code tunnel service install --name "$env:MC_ID" --accept-server-license-terms
