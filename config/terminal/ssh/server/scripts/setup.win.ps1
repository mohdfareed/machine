#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

# Use Scoop's stable launcher, which follows package upgrades without a junction.
$shimDirectory = Split-Path -Parent (Get-Command scoop -ErrorAction Stop).Source
$defaultShell = Join-Path $shimDirectory 'pwsh.exe'
if (-not (Test-Path -LiteralPath $defaultShell -PathType Leaf)) {
    throw "PowerShell executable not found: $defaultShell"
}

Write-Host "configuring OpenSSH PowerShell..."
Invoke-Admin {
    # Set the default shell for OpenSSH to PowerShell 7.
    param($defaultShell)
    New-ItemProperty `
        -Path "HKLM:\SOFTWARE\OpenSSH" `
        -Name DefaultShell `
        -Value $defaultShell `
        -PropertyType String `
        -Force | Out-Null

    # Use the shared per-user allowlist for administrator accounts too.
    $sshdConfig = "$env:ProgramData\ssh\sshd_config"
    (Get-Content $sshdConfig) -replace '^(Match Group administrators)', '#$1' `
        -replace '^(\s*AuthorizedKeysFile __PROGRAMDATA__)', '#$1' |

    Set-Content $sshdConfig
    Restart-Service sshd
} -ArgumentList $defaultShell
