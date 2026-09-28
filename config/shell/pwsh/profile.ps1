#!/usr/bin/env pwsh

# Load public variables prepared by deployment.
$ConfigHome = Split-Path -Parent $PROFILE.CurrentUserAllHosts
. (Join-Path $ConfigHome "env.mc.ps1")

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Environment
# ═════════════════════════════════════════════════════════════════════════════

# Define environment variables.
$env:EDITOR = 'micro'
$env:VISUAL = 'zed --wait'
$env:PIP_REQUIRE_VIRTUALENV = $true
$env:GOPATH = Join-Path $HOME '.go'

# Define binary paths.
$env:PATH += "$([IO.Path]::PathSeparator)$HOME/.local/bin"
$env:PATH += "$([IO.Path]::PathSeparator)$HOME/.docker/bin"
$env:PATH += [IO.Path]::PathSeparator + (Join-Path $env:GOPATH 'bin')

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Configuration
# ═════════════════════════════════════════════════════════════════════════════

# Activate Homebrew (ARM macOS and WSL).
foreach ($brew in @(
    '/opt/homebrew/bin/brew', '/home/linuxbrew/.linuxbrew/bin/brew'
)) {
    if (Test-Path $brew -PathType Leaf) {
        & $brew shellenv pwsh | Invoke-Expression
        break
    }
}
Remove-Variable brew -ErrorAction SilentlyContinue

# Load completions.
. (Join-Path $ConfigHome "completions.ps1")

# Initialize starship prompt.
Invoke-Expression (&starship init powershell)

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Infrastructure
# ═════════════════════════════════════════════════════════════════════════════

# Load user aliases.
. (Join-Path $ConfigHome "aliases.ps1")

# Load machine-specific extras.
$mcProfile = Join-Path $ConfigHome "profile.mc.ps1"
if (Test-Path $mcProfile -PathType Leaf) {
    . $mcProfile
}
Remove-Variable configHome, mcProfile -ErrorAction SilentlyContinue
