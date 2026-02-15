$ErrorActionPreference = "Stop"

# Bootstrap: irm https://raw.githubusercontent.com/mohdfareed/machine/main/bootstrap.ps1 | iex
# Requires: git, curl

$Repo = if ($env:MC_ROOT) { $env:MC_ROOT } else { "$HOME\.machine" }

# ensure uv is available
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv not found. Installing uv..."
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    Write-Host "uv installed. Please run this script again."
    Exit 1
}

# clone repo if needed
if (-not (Test-Path "$Repo\.git")) {
    git clone https://github.com/mohdfareed/machine.git $Repo
}

# install the cli tool
uv tool install $Repo --force
Write-Host "Done. Run 'mc --help' to get started."
