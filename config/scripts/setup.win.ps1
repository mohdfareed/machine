Write-Host "setting up windows tools..."

# set default ssh shell
$command = @'
New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" \
    -Name DefaultShell \
    -Value "$((Get-Command powershell.exe).Source)" \
    -PropertyType String -Force
'@
$encodedCommand = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($command))
Start-Process powershell.exe -Verb RunAs -ArgumentList "-NoProfile -EncodedCommand $encodedCommand"


# wsl
$feature = Microsoft-Windows-Subsystem-Linux
$wslFeature = Get-WindowsOptionalFeature -Online -FeatureName $feature
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
