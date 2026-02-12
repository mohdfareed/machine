# Bootstrap: irm https://raw.githubusercontent.com/mohdfareed/machine/main/bootstrap.ps1 | iex
# Requires: git

$ErrorActionPreference = "Stop"

$Repo = if ($env:MC_ROOT) { $env:MC_ROOT } else { "$HOME\.machine" }
$UvTmp = "$env:TEMP\uv-bootstrap"
$Uv = $null

# ensure uv is available
if (Get-Command uv -ErrorAction SilentlyContinue) {
    $Uv = "uv"
}
else {
    $env:UV_INSTALL_DIR = $UvTmp
    $env:UV_NO_MODIFY_PATH = "1"
    & ([scriptblock]::Create((Invoke-RestMethod https://astral.sh/uv/install.ps1)))
    $Uv = "$UvTmp\uv.exe"
}

# clone repo if needed
if (-not (Test-Path "$Repo\.git")) {
    git clone https://github.com/mohdfareed/machine.git $Repo
}

# install the cli tool
& $Uv tool install $Repo --force

# clean up temp uv
if ($Uv -ne "uv" -and (Test-Path $UvTmp)) {
    Remove-Item $UvTmp -Recurse -Force
}

Write-Host "Done. Run 'mc --help' to get started."
