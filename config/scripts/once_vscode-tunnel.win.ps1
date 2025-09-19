#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

$tunnel = $env:MACHINE_ID
if ([string]::IsNullOrWhiteSpace($tunnel)) {
    Write-Warning 'MACHINE_ID is not set; skipping vscode tunnel setup.'
    exit 0
}

if ($env:CODESPACES -eq 'true') {
    Write-Host 'detected codespaces environment, skipping vscode tunnel setup'
    exit 0
}

Write-Output "setting up vscode tunnel: $tunnel"
code tunnel service install --name "$tunnel" --accept-server-license-terms
