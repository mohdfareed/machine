#!/usr/bin/env pwsh
Import-Module PSReadLine
# NOTE: Avoid the preview regression: https://github.com/kelleyma49/PSFzf/issues/380
Import-Module PSFzf -RequiredVersion 2.7.9
Import-Module posh-git

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Infrastructure
# ═════════════════════════════════════════════════════════════════════════════

# Load public variables prepared by deployment.
$configHome = if ($IsWindows) {
    $env:LOCALAPPDATA
} elseif ($env:XDG_CONFIG_HOME) {
    $env:XDG_CONFIG_HOME
} else {
    Join-Path $HOME '.config'
}

$machineEnvironment = Join-Path $configHome 'mc/env.ps1'
if (Test-Path -LiteralPath $machineEnvironment -PathType Leaf) {
    . $machineEnvironment
}

Remove-Variable configHome, machineEnvironment

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Environment
# ═════════════════════════════════════════════════════════════════════════════

# Load Homebrew environment.
$brewBins = @('/opt/homebrew/bin/brew', '/home/linuxbrew/.linuxbrew/bin/brew')
foreach ($brew in $brewBins) {
    if (Test-Path $brew -PathType Leaf) {
        & $brew shellenv pwsh | Invoke-Expression
        break
    }
}

# Load Homebrew completions.
if (Test-Path ($comp = "$env:HOMEBREW_PREFIX/share/pwsh/completions")) {
    foreach ($f in Get-ChildItem -Path $comp -Filter '*.ps1' -File) {
        . $f
    }
}

Remove-Variable brewBins -ErrorAction SilentlyContinue
Remove-Variable brew -ErrorAction SilentlyContinue
Remove-Variable comp -ErrorAction SilentlyContinue
Remove-Variable f -ErrorAction SilentlyContinue

$env:PIP_REQUIRE_VIRTUALENV = $true
$env:GOPATH = Join-Path $HOME 'go'

$env:PATH += "$([IO.Path]::PathSeparator)$HOME/.local/bin"
$env:PATH += "$([IO.Path]::PathSeparator)$HOME/.docker/bin"
$env:PATH += "$([IO.Path]::PathSeparator)$GOPATH/bin"

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Configuration
# ═════════════════════════════════════════════════════════════════════════════

# Load user-defined completions.
$completionDirectory = Join-Path (Split-Path -Parent $PROFILE.CurrentUserAllHosts) 'completions'
Get-ChildItem -LiteralPath $completionDirectory -Filter '*.ps1' -File -ErrorAction SilentlyContinue |
    ForEach-Object { . $_.FullName }
Remove-Variable completionDirectory

# Tool completions.
if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv generate-shell-completion powershell | Out-String | Invoke-Expression
}
if (Get-Command uvx -ErrorAction SilentlyContinue) {
    uvx --generate-shell-completion powershell | Out-String | Invoke-Expression
}
if (Get-Command dotnet -ErrorAction SilentlyContinue) {
    dotnet completions script pwsh | Out-String | Invoke-Expression
}

# Enable auto-suggestions and tab-compeltions
Set-PSReadLineOption -PredictionSource History
Set-PSReadLineKeyHandler -Key Tab -ScriptBlock { Invoke-FzfTabCompletion }
Set-PsFzfOption -TabExpansion

# Enable ctrl-r, ctrl-t, alt-c fzf bindings.
Set-PsFzfOption -PSReadlineChordProvider 'Ctrl+t'
Set-PsFzfOption -PSReadlineChordReverseHistory 'Ctrl+r'
Set-PsFzfOption -PSReadlineChordSetLocation 'Alt+c'

# Enable starship theme.
Invoke-Expression (&starship init powershell)

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Infrastructure
# ═════════════════════════════════════════════════════════════════════════════

# functions & aliases
. (Join-Path $PSScriptRoot "aliases.ps1")
# machine-specific extras
$machineProfile = Join-Path (Split-Path -Parent $PROFILE.CurrentUserAllHosts) 'profile.mc.ps1'
if (Test-Path -LiteralPath $machineProfile -PathType Leaf) {
    . $machineProfile
}
Remove-Variable machineProfile
