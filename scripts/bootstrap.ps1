param([switch]$Deploy)
$ErrorActionPreference = "Stop"

# Update the PATH for the current session
function Update-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
    [System.Environment]::GetEnvironmentVariable("Path", "User")
}

$env:MC_HOME = if ($env:MC_HOME) {
    [System.IO.Path]::GetFullPath($env:MC_HOME.Replace("~", $HOME))
}
else {
    "$HOME\.machine"
}

# Resolve python version from .python-version file if it exists
$repo = "https://raw.githubusercontent.com/mohdfareed/machine/main"
$pythonVersion = irm $repo/.python-version

# Ensure git is available
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    winget install "git.git"
    Update-Path
}

# Ensure uv is available
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    winget install "astral-sh.uv"
    Update-Path
}

# Install system dependencies
if (-not (uv python list --only-installed | Select-String $pythonVersion)) {
    Write-Host "Installing Python $pythonVersion..."
    uv python install $pythonVersion
}

# Clone repo if needed
if (-not (Test-Path "$env:MC_HOME\.git")) {
    git clone https://github.com/mohdfareed/machine.git "$env:MC_HOME"
}

# Sync the repo and install the CLI.
uv run --project $env:MC_HOME mc sync

# Deploy only when requested.
if ($Deploy -or $env:MC_BOOTSTRAP_DEPLOY -in @("1", "true")) {
    uv run --project $env:MC_HOME mc deploy
}
