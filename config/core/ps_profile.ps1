#!/usr/bin/env pwsh

# resolve script path
$symlinkPath = $MyInvocation.MyCommand.Definition
$realScriptPath = (Get-Item -LiteralPath $symlinkPath).Target
if (-not $realScriptPath) { $realScriptPath = $symlinkPath }
Remove-Variable -Name "symlinkPath"

# machine path
$config = Split-Path -Parent -Path (Split-Path -Parent -Path $realScriptPath)
$env:MACHINE = Split-Path -Parent -Path $config
[System.Environment]::SetEnvironmentVariable("MACHINE", $env:MACHINE, `
        [System.EnvironmentVariableTarget]::User)
Remove-Variable -Name "realScriptPath"
Remove-Variable -Name "config"

# set execution policy
if ($IsWindows) {
    Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
}

# homebrew
if (Test-Path -Path "/opt/homebrew/bin/brew") {
    $(/opt/homebrew/bin/brew shellenv) | Invoke-Expression
}

# fnm (windows node version manager)
if ($IsWindows -and -not (Get-Command -Name "fnm" -ErrorAction SilentlyContinue)) {
    fnm env --use-on-cd | Out-String | Invoke-Expression
}

# dotnet completions
Register-ArgumentCompleter -Native -CommandName dotnet -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    dotnet complete --position $cursorPosition "$commandAst" | ForEach-Object {
        [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
    }
}

# oh-my-posh theme
if (-not (Get-Command -Name "oh-my-posh" -ErrorAction SilentlyContinue)) {
    $installScript = 'https://ohmyposh.dev/install.ps1'
    $webClient = New-Object System.Net.WebClient
    Set-ExecutionPolicy Bypass -Scope Process -Force
    Invoke-Expression ($webClient.DownloadString($installScript))
    Remove-Variable -Name "installScript"; Remove-Variable -Name "webClient"
}
$theme = "$env:POSH_THEMES_PATH/pure.omp.json"
oh-my-posh init pwsh --config "$theme" | Invoke-Expression
Remove-Variable -Name "theme"
