$ErrorActionPreference = "Stop"

# Bootstrap: irm https://raw.githubusercontent.com/mohdfareed/machine/main/bootstrap.ps1 | iex
$Root = if ($env:MC_ROOT) { $env:MC_ROOT } else { "$HOME\.machine" }

# clone repo if needed
winget install "git.git"
if (-not (Test-Path "$Root\.git")) {
    git clone https://github.com/mohdfareed/machine.git "$Root"
}

# install the cli tool
winget install "astral-sh.uv"
uv tool install $Root --force
Write-Host "Done. Run 'mc --help' to get started."
