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
