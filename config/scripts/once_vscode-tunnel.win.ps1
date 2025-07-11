#!/usr/bin/env pwsh

$tunnel = $env:MACHINE_ID

Write-Output "setting up vscode tunnel: $tunnel"
code tunnel service install --name "$tunnel" --accept-server-license-terms
Write-Output "vscode tunnel setup completed"
