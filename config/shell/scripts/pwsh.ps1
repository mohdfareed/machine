#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

# Use the interactive shell even when setup starts in Windows PowerShell.
if ($PSVersionTable.PSVersion.Major -lt 7) {
    & pwsh -NoProfile -File $PSCommandPath
    exit $LASTEXITCODE
}

# Install interactive modules for the current PowerShell 7 user.
Install-Module -Name PSFzf -RequiredVersion 2.7.9 -Scope CurrentUser
Install-Module -Name posh-git -Scope CurrentUser

# Set up the completion directory.
$completions = Join-Path (Split-Path -Parent $PROFILE.CurrentUserAllHosts) 'completions'
New-Item -ItemType Directory -Path $directory -Force | Out-Null

# Install mc completion.
$env:_MC_COMPLETE = 'source_powershell'
try {
    $completion = & mc
    if ($LASTEXITCODE -ne 0) { throw 'Could not generate mc completion.' }
}
finally {
    Remove-Item Env:_MC_COMPLETE
}
$completion | Set-Content -LiteralPath (Join-Path $completions 'mc.ps1') -Encoding utf8
