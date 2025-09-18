Write-Host "setting up windows tools..."

# install windows features
Write-Host "enabling windows features..."
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-RemoteDesktopConnection
Enable-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform
Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform
Enable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol

# wsl
Write-Host "installing wsl..."
wsl --install
Write-Host "updating wsl..."
wsl --update

# scoop
if (-not (Get-Command scoop -ErrorAction SilentlyContinue)) {
    Write-Host "installing scoop..."
    Invoke-WebRequest -Uri https://get.scoop.sh | Invoke-Expression
}

# install ssh services if not present
if (-not (Get-Service -Name sshd -ErrorAction SilentlyContinue)) {
    Write-Host "installing ssh services..."
    Add-WindowsCapability -Online -Name OpenSSH.Client
    Add-WindowsCapability -Online -Name OpenSSH.Server
}

# verify ssh agent is available
if (-not (Get-Service -Name sshd -ErrorAction SilentlyContinue)) {
    Write-Error "sshd service is not available."
    exit 1
}

# set default ssh shell
Write-Host "configuring ssh services..."
$pwsh = "C:\Program Files\PowerShell\7\pwsh.exe"
New-ItemProperty -Path 'HKLM:\SOFTWARE\OpenSSH' -Name DefaultShell \
-Value $pwsh -PropertyType String -Force
Restart-Service sshd -Force

# ensure ssh agent starts automatically and is running
Set-Service -Name sshd -StartupType 'Automatic'
if ((Get-Service -Name sshd).Status -ne 'Running') {
    Write-Host "starting ssh server service..."
    Start-Service sshd
}
Write-Host "ssh-agent is enabled and running."

Write-Host "windows set up successfully"
