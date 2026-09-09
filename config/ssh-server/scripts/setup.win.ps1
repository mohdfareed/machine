#! /usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

Write-Host "installing OpenSSH..."
Invoke-Admin {
    Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
    Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
}

Write-Host "configuring SSH services..."
Invoke-Admin {
    Get-Service -Name sshd | Set-Service -StartupType Automatic
    Get-Service -Name ssh-agent | Set-Service -StartupType Automatic
}

Write-Host "fixing OpenSSH PowerShell configuration..."
Invoke-Admin {
    # PowerShell 7 MSIX aliases cannot be used as the OpenSSH system shell.
    New-ItemProperty `
        -Path "HKLM:\SOFTWARE\OpenSSH" `
        -Name DefaultShell `
        -Value "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" `
        -PropertyType String `
        -Force | Out-Null
}

Write-Host "fixing OpenSSH admin keys configuration..."
Invoke-Admin {
    # Windows OpenSSH overrides authorized_keys for Administrators to a separate
    # file (administrators_authorized_keys), breaking standard pubkey auth.
    $sshdConfig = "$env:ProgramData\ssh\sshd_config"
    (Get-Content $sshdConfig) -replace '^(Match Group administrators)', '#$1' `
        -replace '^(\s*AuthorizedKeysFile __PROGRAMDATA__)', '#$1' |
    Set-Content $sshdConfig
}

Write-Host "restarting SSH service..."
Invoke-Admin {
    Restart-Service sshd
}
