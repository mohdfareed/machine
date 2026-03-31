#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

if (-not $env:MC_ID)
{
    Write-Host "MC_ID is not set; cannot set up vscode tunnel without a hostname"
    exit 1
}

Write-Output "setting up vscode tunnel: $env:MC_ID"
$p = Start-Process -FilePath "code" `
    -ArgumentList "tunnel","service","install","--name",$env:MC_ID,"--accept-server-license-terms" `
    -PassThru

$p.WaitForExit()
if ($p.ExitCode -ne 0)
{
    Write-Host "Failed to install VS Code tunnel service (exit code $($p.ExitCode))"
    exit $p.ExitCode
}
