#!/usr/bin/env pwsh

# Environment
# =============================================================================

$env:PATH += ";$HOME/.local/bin" # user local bin
$env:PIP_REQUIRE_VIRTUALENV = $true  # python

# Configuration
# =============================================================================

# homebrew
if (Test-Path -Path "/opt/homebrew/bin/brew") {
    $(/opt/homebrew/bin/brew shellenv) | Invoke-Expression
} # arm macos
if (Test-Path -Path "/usr/local/bin/brew") {
    $(/usr/local/bin/brew shellenv) | Invoke-Expression
} # intel macos
if (Test-Path -Path "/home/linuxbrew/.linuxbrew/bin/brew") {
    $(/home/linuxbrew/.linuxbrew/bin/brew shellenv) | Invoke-Expression
} # linux/wsl

# oh-my-posh
if ($IsWindows) {
    $theme = "$env:LOCALAPPDATA/Programs/oh-my-posh/themes/pure.omp.json"
}
else {
    $theme = "$((oh-my-posh cache path))/themes/pure.omp.json"
}
oh-my-posh init pwsh --config "$theme" | Invoke-Expression
Remove-Variable -Name "theme"

# Completions
# =============================================================================

# tab-completion
Set-PSReadlineKeyHandler -Key Tab -Function MenuComplete

# homebrew completions
if ((Get-Command brew) -and (Test-Path ($completions = "$(brew --prefix)/share/pwsh/completions"))) {
    foreach ($f in Get-ChildItem -Path $completions -File) {
        . $f
    }
}

# dotnet completions
Register-ArgumentCompleter -Native -CommandName dotnet -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    dotnet complete --position $cursorPosition "$commandAst" | ForEach-Object {
        [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
    }
}

# uv completions (python version manager)
if (Get-Command uv -ErrorAction SilentlyContinue) {
    (& uv generate-shell-completion powershell) | Out-String | Invoke-Expression
    (& uvx --generate-shell-completion powershell) | Out-String | Invoke-Expression
}

# Infrastructure
# =============================================================================

# private env
if (Test-Path "~/.env.ps1") {
    . "~/.env.ps1"
}

# functions & aliases
. "~/.config/powershell/aliases.ps1"

# machine-specific extras
if (Test-Path "~/.config/powershell/profile.local.ps1") {
    . "~/.config/powershell/profile.local.ps1"
}
