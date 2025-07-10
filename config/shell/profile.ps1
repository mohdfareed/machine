#!/usr/bin/env pwsh

# configuration
Set-PSReadlineKeyHandler -Key Tab -Function MenuComplete

# PATH
$env:PATH += ";C:\Program Files\LLVM\bin" # c compiler
$env:PATH += ";$HOME/.local/bin" # user local bin

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
$theme = Join-Path (oh-my-posh cache path) 'themes/pure.omp.json'
oh-my-posh init pwsh --config "$theme" | Invoke-Expression
Remove-Variable -Name "theme"

# uv (python version manager)
if (Get-Command uv -ErrorAction SilentlyContinue) {
    (& uv generate-shell-completion powershell) | Out-String | Invoke-Expression
    (& uvx --generate-shell-completion powershell) | Out-String | Invoke-Expression
}

# dotnet completions
Register-ArgumentCompleter -Native -CommandName dotnet -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    dotnet complete --position $cursorPosition "$commandAst" | ForEach-Object {
        [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
    }
}


# MARK: Aliases
# =============================================================================

function GenSSHKey {
    param (
        [Parameter(Mandatory = $true)][string]$KeyName,
        [Parameter(Mandatory = $true)][string]$Email,
        [Parameter(Mandatory = $true)][SecureString]$Passphrase
    )
    ssh-keygen -t ed25519 -f "$HOME/.ssh/$KeyName" -C "$Email" -N "$Passphrase"
}
