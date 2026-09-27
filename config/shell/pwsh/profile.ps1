#!/usr/bin/env pwsh
Import-Module PSReadLine
# NOTE: Avoid the preview regression: https://github.com/kelleyma49/PSFzf/issues/380
Import-Module PSFzf -RequiredVersion 2.7.9

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Infrastructure
# ═════════════════════════════════════════════════════════════════════════════
$ConfigPath = Split-Path -Parent $PROFILE.CurrentUserAllHosts

# Load public variables prepared by deployment.
$machineEnvironment = Join-Path $ConfigPath 'mc/env.ps1'
if (Test-Path -LiteralPath $machineEnvironment -PathType Leaf) {
    . $machineEnvironment
}
Remove-Variable machineEnvironment

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Environment
# ═════════════════════════════════════════════════════════════════════════════

# Activate Homebrew (ARM macOS and WSL).
$brewBins = @('/opt/homebrew/bin/brew', '/home/linuxbrew/.linuxbrew/bin/brew')
foreach ($brew in $brewBins) {
    if (Test-Path $brew -PathType Leaf) {
        & $brew shellenv pwsh | Invoke-Expression
        break
    }
}

Remove-Variable brewBins -ErrorAction SilentlyContinue
Remove-Variable brew -ErrorAction SilentlyContinue

# Define environment variables.
$env:PIP_REQUIRE_VIRTUALENV = $true
$env:GOPATH = Join-Path $HOME '.go'

# Define binary paths.
$env:PATH += "$([IO.Path]::PathSeparator)$HOME/.local/bin"
$env:PATH += "$([IO.Path]::PathSeparator)$HOME/.docker/bin"
$env:PATH += [IO.Path]::PathSeparator + (Join-Path $env:GOPATH 'bin')

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Configuration
# ═════════════════════════════════════════════════════════════════════════════

# Enable auto-suggestions and menu completion.
Set-PSReadLineOption -PredictionSource History
Set-PSReadLineOption -Colors @{ "Selection" = "`e[7m" }
Set-PSReadLineKeyHandler -Key Tab -Function MenuComplete
Set-PSReadLineKeyHandler -Key Shift+Tab -ScriptBlock { Invoke-FzfTabCompletion }

# Enable fzf bindings.
Set-PsFzfOption -TabExpansion
Set-PsFzfOption -PSReadlineChordProvider 'Ctrl+t'
Set-PsFzfOption -PSReadlineChordReverseHistory 'Ctrl+r'
Set-PsFzfOption -PSReadlineChordSetLocation 'Alt+c'
Set-PsFzfOption -PSReadlineChordReverseHistoryArgs 'Alt+a'

# Enable starship prompt.
Invoke-Expression (&starship init powershell)

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Completions
# ═════════════════════════════════════════════════════════════════════════════

# Load Homebrew completions.
if (Test-Path ($comp = "$env:HOMEBREW_PREFIX/share/pwsh/completions")) {
    foreach ($f in Get-ChildItem -Path $comp -Filter '*.ps1' -File) {
        . $f
    }
}
Remove-Variable comp -ErrorAction SilentlyContinue
Remove-Variable f -ErrorAction SilentlyContinue

# Load tool completions.
if (Get-Command uv -ErrorAction SilentlyContinue) {
    mc --show-completion | Out-String | Invoke-Expression
}
if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv generate-shell-completion powershell | Out-String | Invoke-Expression
}
if (Get-Command uvx -ErrorAction SilentlyContinue) {
    uvx --generate-shell-completion powershell | Out-String | Invoke-Expression
}
if (Get-Command carapace -ErrorAction SilentlyContinue) {
    carapace _carapace powershell | Out-String | Invoke-Expression
}

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Infrastructure
# ═════════════════════════════════════════════════════════════════════════════

# Load functions and aliases.
. (Join-Path $ConfigPath "aliases.ps1")

# Load machine-specific extras.
$machineProfile = Join-Path $ConfigPath 'profile.mc.ps1'
if (Test-Path -LiteralPath $machineProfile -PathType Leaf) {
    . $machineProfile
}

Remove-Variable machineProfile
Remove-Variable ConfigPath
