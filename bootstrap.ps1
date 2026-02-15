#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$env:MC_HOME = if ($env:MC_HOME) { $env:MC_HOME } else { "$HOME\.machine" }

# Ensure git and uv are available
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    winget install "git.git"
    Write-Host "git installed. Restart your shell and re-run this script."
    Exit 0
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    winget install "astral-sh.uv"
    Write-Host "uv installed. Restart your shell and re-run this script."
    Exit 0
}

# Clone repo if needed
if (-not (Test-Path "$env:MC_HOME\.git")) {
    git clone https://github.com/mohdfareed/machine.git "$env:MC_HOME"
}

# Install the cli tool
uv tool install $env:MC_HOME --editable --force
Write-Host "Installed machine cli. Restart shell and run 'mc --help' for more info."
