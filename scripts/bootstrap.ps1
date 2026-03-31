#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$env:MC_HOME = if ($env:MC_HOME)
{ [System.IO.Path]::GetFullPath($env:MC_HOME.Replace("~", $HOME))
} else
{ "$HOME\.machine"
}

# Update the PATH for the current session
function Update-Path
{
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
    [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# Ensure git and uv are available
if (-not (Get-Command git -ErrorAction SilentlyContinue))
{
    winget install "git.git"
    Update-Path
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue))
{
    winget install "astral-sh.uv"
    Write-Host "uv installed. Restart your shell and re-run this script."
    Update-Path
} else
{
    try # update uv if already installed
    { uv self update 2>$ull
    } catch
    {
    }
}

# Install system dependencies
if (-not (uv python list --only-installed | Select-String "3.14"))
{
    Write-Host "Installing Python 3.14..."
    uv python install 3.14
}

# Clone repo if needed
if (-not (Test-Path "$env:MC_HOME\.git"))
{
    git clone https://github.com/mohdfareed/machine.git "$env:MC_HOME"
}

# Install the cli tool
uv tool install $env:MC_HOME --editable --force
Write-Host "Installed machine cli. Run 'mc --help' for more info."
