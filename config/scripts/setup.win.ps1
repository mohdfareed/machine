Write-Host "setting up windows tools..."

# set default ssh shell
$command = 'New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell -Value (Get-Command powershell.exe).Source -PropertyType String -Force'
Start-Process -FilePath "powershell.exe" `
    -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $command `
    -Verb RunAs -Wait

# restart the SSH service so the change takes effect
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
