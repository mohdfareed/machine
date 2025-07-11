Write-Host "setting up windows tools..."

# set default ssh shell
New-ItemProperty `
    -Path "HKLM:\HKEY_LOCAL_MACHINE\SOFTWARE\OpenSSH" `
    -Name DefaultShell `
    -Value $(Get-Command powershell.exe).Source `
    -PropertyType String -Force

# update wsl and scoop
wsl --update
if (-not (Get-Command scoop -ErrorAction SilentlyContinue)) {
    Invoke-WebRequest -Uri https://get.scoop.sh | Invoke-Expression
}
else {
    scoop update
}

Write-Host "windows set up successfully"
