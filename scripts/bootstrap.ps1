#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"

# Update the PATH for the current session.
function Update-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
    [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# ═════════════════════════════════════════════════════════════════════════════
# Dependencies
# ═════════════════════════════════════════════════════════════════════════════

# Ensure git is available.
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    winget install "git.git"
    Update-Path
}

# Ensure uv is available.
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    winget install "astral-sh.uv"
    Update-Path
}

# ═════════════════════════════════════════════════════════════════════════════
# Bootstrap
# ═════════════════════════════════════════════════════════════════════════════

# Resolve machine repo directory.
$env:MC_HOME = if ($env:MC_HOME) {
    [System.IO.Path]::GetFullPath($env:MC_HOME.Replace("~", $HOME))
}
else {
    "$HOME\.machine"
}

# Clone repo if needed.
if (-not (Test-Path "$env:MC_HOME\.git")) {
    git clone https://github.com/mohdfareed/machine.git "$env:MC_HOME"
}

# Sync and deploy the repo.
uv run --project $env:MC_HOME mc sync
uv run --project $env:MC_HOME mc deploy
