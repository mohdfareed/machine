$ErrorActionPreference = "Stop"

# Bootstrap: irm https://raw.githubusercontent.com/mohdfareed/machine/main/bootstrap.ps1 | iex
$Root = if ($env:MC_ROOT) { $env:MC_ROOT } else { "$HOME\.machine" }

# ensure git and uv are available
winget install "git.git" "astral-sh.uv"

# clone repo if needed
if (-not (Test-Path "$Root\.git")) {
    Write-Host "Cloning repository..."
    git clone https://github.com/mohdfareed/machine.git "$Root"
}

# install the cli tool
uv tool install $Root --force
Write-Host "Done. Run 'mc --help' to get started."
