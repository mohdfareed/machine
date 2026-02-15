#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$env:MC_HOME = if ($env:MC_HOME) { $env:MC_HOME } else { "$HOME\.machine" }
function Update-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
    [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# Ensure git and uv are available
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    winget install "git.git"
    Update-Path
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    winget install "astral-sh.uv"
    Update-Path
}

# Clone repo if needed
if (-not (Test-Path "$env:MC_HOME\.git")) {
    git clone https://github.com/mohdfareed/machine.git "$env:MC_HOME"
}

# Install the cli tool
uv tool install $env:MC_HOME --editable --force
Update-Path
Write-Host "Installed machine cli. Run 'mc --help' for more info."
