#!/usr/bin/env pwsh
param([switch]$Admin, [string]$DefaultShell)
$ErrorActionPreference = 'Stop'

if ($Admin) {
    Write-Host "configuring OpenSSH PowerShell..."
    # Set the default shell for OpenSSH to PowerShell 7.
    New-ItemProperty `
        -Path "HKLM:\SOFTWARE\OpenSSH" `
        -Name DefaultShell `
        -Value $DefaultShell `
        -PropertyType String `
        -Force | Out-Null

    # Use the shared per-user allowlist for administrator accounts too.
    $sshdConfig = "$env:ProgramData\ssh\sshd_config"
    (Get-Content $sshdConfig) -replace '^(Match Group administrators)', '#$1' `
        -replace '^(\s*AuthorizedKeysFile __PROGRAMDATA__)', '#$1' |

    Set-Content $sshdConfig
    Restart-Service sshd
    Read-Host 'Press Enter to exit'
    return
}

# Use Scoop's stable launcher, which follows package upgrades without a junction.
$shimDirectory = Split-Path -Parent (Get-Command scoop -ErrorAction Stop).Source
$DefaultShell = Join-Path $shimDirectory 'pwsh.exe'
if (-not (Test-Path -LiteralPath $DefaultShell -PathType Leaf)) {
    throw "PowerShell executable not found: $DefaultShell"
}

# Resolve the user's launcher before UAC; an alternate admin may have a different home.
$arguments = @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"", '-Admin',
    '-DefaultShell', "`"$DefaultShell`""
)
$process = Start-Process -FilePath (Get-Process -Id $PID).Path -ArgumentList $arguments `
    -Verb RunAs -Wait -PassThru
if ($process.ExitCode -ne 0) { exit $process.ExitCode }
