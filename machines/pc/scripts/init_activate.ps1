#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

Write-Host "activating windows..."
Invoke-RestMethod https://get.activated.win | Invoke-Expression
