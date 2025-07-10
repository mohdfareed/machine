Write-Host "updating windows tools..."

# set default ssh shell
New-ItemProperty `
    -Path "HKLM:\HKEY_LOCAL_MACHINE\SOFTWARE\OpenSSH" `
    -Name DefaultShell `
    -Value $(Get-Command powershell.exe).Source `
    -PropertyType String -Force

# update windows tools
wsl --update
winget upgrade --all --include-unknown
if (Get-Command scoop -ErrorAction SilentlyContinue) {
    scoop update
    scoop update *
    scoop cleanup *
}

Write-Host "windows tools updated successfully"
