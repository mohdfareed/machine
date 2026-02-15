$ErrorActionPreference = "Stop"

$Root = if ($env:MC_ROOT) { $env:MC_ROOT } else { "$HOME\.machine" }
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
if (-not (Test-Path "$Root\.git")) {
    git clone https://github.com/mohdfareed/machine.git "$Root"
}

# Install the cli tool
uv tool install $Root --force
Update-Path
Write-Host "Installed machine cli. Run 'mc --help' for more info."
