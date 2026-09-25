#!/usr/bin/env pwsh
Import-Module PSReadLine
Import-Module PSFzf
Import-Module posh-git

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Environment
# ═════════════════════════════════════════════════════════════════════════════

# User-installed binaries.
$env:PATH += "$([IO.Path]::PathSeparator)$HOME/.local/bin"
# Python - require virtualenv.
$env:PIP_REQUIRE_VIRTUALENV = $true

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
# MARK: Homebrew
# ═════════════════════════════════════════════════════════════════════════════

# Homebrew bin paths.
$brewBins = @(
    '/opt/homebrew/bin/brew',
    '/usr/local/bin/brew',
    '/home/linuxbrew/.linuxbrew/bin/brew'
)

# Load Homebrew environment.
foreach ($brew in $brewBins) {
    if (-not (Test-Path $brew -PathType Leaf)) {
        continue
    }

    $brewEnv = & $brew shellenv pwsh
    if ($brewEnv) {
        $brewEnv | Out-String | Invoke-Expression
    }
    break
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

# Enable auto-suggestions.
Set-PSReadLineOption -PredictionSource History
# Enable fzf-based tab completion.
Set-PSReadLineKeyHandler -Key Tab -ScriptBlock { Invoke-FzfTabCompletion }
# Enable fzf tab expansion.
Set-PsFzfOption -TabExpansion

# Enable ctrl-r, ctrl-t, alt-c fzf bindings.
Set-PsFzfOption -PSReadlineChordProvider 'Ctrl+t'
Set-PsFzfOption -PSReadlineChordReverseHistory 'Ctrl+r'
Set-PsFzfOption -PSReadlineChordSetLocation 'Alt+c'
Set-PsFzfOption -TabCompletionPreviewWindow 'bottom|hidden'

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
