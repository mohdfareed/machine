#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

# Use the interactive shell even when setup starts in Windows PowerShell.
if ($PSVersionTable.PSVersion.Major -lt 7) {
    & pwsh -NoProfile -File $PSCommandPath
    exit $LASTEXITCODE
}

# Install mc completion.
$ConfigHome = Split-Path -Parent $PROFILE.CurrentUserAllHosts
New-Item -ItemType Directory -Force "$ConfigHome/Completions" | Out-Null
mc --show-completion > "$ConfigHome/Completions/mc.ps1"

if (-not $IsWindows) {
    # Add Carapace bridge to brew zsh completion.
    $bridgeDir = Join-Path $HOME '.config/carapace/bridge/zsh'
    New-Item -ItemType Directory -Path $bridgeDir -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $bridgeDir '.zshrc') -Encoding utf8 `
        -Value 'fpath=("${HOMEBREW_PREFIX:?}/share/zsh/site-functions" $fpath)'
}

# Install interactive modules for the current PowerShell 7 user.
Install-Module -Name PSFzf -Scope CurrentUser
Install-Module -Name PSCompletions -Scope CurrentUser
# Update-Help -ErrorAction Continue # TODO: Move to `up_` script due to speed.
psc config menu filter_mode subsequence
psc update
