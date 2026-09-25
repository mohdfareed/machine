#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"
param([switch]$Deploy)

# ═════════════════════════════════════════════════════════════════════════════
# Dependencies
# ═════════════════════════════════════════════════════════════════════════════

# Update the PATH for the current session.
function Update-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
    [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# Ensure winget is available.
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    if (-not (Get-Command Add-AppxPackage -ErrorAction SilentlyContinue)) {
        Write-Error "App Installer is missing."
        Write-Host "Install from: https://apps.microsoft.com/detail/9nblggh4nns1"
        exit 1
    }

    Add-AppxPackage -RegisterByFamilyName -MainPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe
    Update-Path
}

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

# Install `mc` with uv, forcing an update if already installed.
uv tool install $env:MC_HOME --editable --force
if ($Deploy) {
    uv run --project $env:MC_HOME mc deploy
}
