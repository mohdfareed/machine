param (
    [switch]$EnvOnly = $false
)

# Environment (shared across machines)
# =============================================================================

# set the machine repo path
$script = (Get-Item -Path $MyInvocation.MyCommand.Path).Target
if (-not $script) {
    $script = $MyInvocation.MyCommand.Path
}
$env:MACHINE = Resolve-Path "$script/../.." # ps_profile -> config -> machine
Remove-Variable -Name "script"

# private environment
$env:SSH_KEYS = "$env:MACHINE/config/keys"
$env:PRIVATE_ENV = "$env:MACHINE/config/private.ps1"
if (Test-Path -Path $env:PRIVATE_ENV) {
    . $env:PRIVATE_ENV
}

# misc
$env:PIP_REQUIRE_VIRTUALENV = "true"
if ($EnvOnly) { return } # don't run the rest of the script

# Shell Setup
# =============================================================================

# set execution policy
if ($IsWindows) {
    Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
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

# load homebrew in powershell if on unix
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
