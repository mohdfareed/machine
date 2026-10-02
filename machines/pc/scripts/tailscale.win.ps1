#!/usr/bin/env pwsh
param([switch]$Admin, [string]$TailscalePath)
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

if ($Admin) {
    & $TailscalePath set --unattended=true
    $exitCode = $LASTEXITCODE
    Read-Host 'Press Enter to exit'
    exit $exitCode
}
if (-not (Get-Command tailscale -ErrorAction SilentlyContinue)) {
    throw 'tailscale not found'
}

tailscale status *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host 'connecting to tailscale...'
    tailscale up
    if ($LASTEXITCODE -ne 0) {
        throw 'tailscale connection failed'
    }
}

# Keep remote access available after logout and before sign-in.
$TailscalePath = (Get-Command tailscale).Source
$arguments = @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"", '-Admin',
    '-TailscalePath', "`"$TailscalePath`""
)
$process = Start-Process -FilePath (Get-Process -Id $PID).Path -ArgumentList $arguments `
    -Verb RunAs -Wait -PassThru
if ($process.ExitCode -ne 0) { throw 'tailscale unattended setup failed' }
