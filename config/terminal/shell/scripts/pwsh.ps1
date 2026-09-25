#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

# Use the interactive shell even when setup starts in Windows PowerShell.
if ($PSVersionTable.PSVersion.Major -lt 7) {
    & pwsh -NoProfile -File $PSCommandPath
    exit $LASTEXITCODE
}

# Install interactive modules for the current PowerShell 7 user.
Install-Module -Name PSFzf -Scope CurrentUser
Install-Module -Name posh-git -Scope CurrentUser

# Typer's installer appends to the profile and changes policy; overwrite one file instead.
$env:_MC_COMPLETE = 'source_powershell'
try {
    $completion = & mc
    if ($LASTEXITCODE -ne 0) { throw 'Could not generate mc completion.' }
}
finally {
    Remove-Item Env:_MC_COMPLETE
}
$directory = Join-Path (Split-Path -Parent $PROFILE.CurrentUserAllHosts) 'completions'
New-Item -ItemType Directory -Path $directory -Force | Out-Null
$completion | Set-Content -LiteralPath (Join-Path $directory 'mc.ps1') -Encoding utf8
