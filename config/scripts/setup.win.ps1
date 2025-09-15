Write-Host "setting up windows tools..."

# set default ssh shell
$pwsh = "C:\Program Files\PowerShell\7\pwsh.exe"
New-ItemProperty -Path 'HKLM:\SOFTWARE\OpenSSH' -Name DefaultShell -Value $pwsh -PropertyType String -Force
Restart-Service sshd -Force

# wsl
$wslFeature = Get-WindowsOptionalFeature -Online `
    -FeatureName Microsoft-Windows-Subsystem-Linux
if ($wslFeature.State -eq "Enabled") {
    wsl --update
}
else {
    wsl --install
}

# scoop
if (-not (Get-Command scoop -ErrorAction SilentlyContinue)) {
    Invoke-WebRequest -Uri https://get.scoop.sh | Invoke-Expression
}

Write-Host "windows set up successfully"
