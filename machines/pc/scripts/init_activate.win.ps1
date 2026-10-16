#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

if ($env:SSH_CONNECTION) {
    Write-Warning 'Skipping Windows activation over SSH.'
    return
}

Write-Host "activating windows..."
Invoke-RestMethod https://get.activated.win | Invoke-Expression
