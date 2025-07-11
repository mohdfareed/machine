Write-Host "setting up windows tools..."

# set default ssh shell
# FIXME: requested registry access is not allowed
New-ItemProperty `
    -Path "HKLM:\HKEY_LOCAL_MACHINE\SOFTWARE\OpenSSH" `
    -Name DefaultShell `
    -Value $(Get-Command powershell.exe).Source `
    -PropertyType String -Force

# wsl
wsl --update
wsl --install # FIXME: freezes then throws error that distro exists

# scoop
if (-not (Get-Command scoop -ErrorAction SilentlyContinue)) {
    Invoke-WebRequest -Uri https://get.scoop.sh | Invoke-Expression
}

Write-Host "windows set up successfully"
