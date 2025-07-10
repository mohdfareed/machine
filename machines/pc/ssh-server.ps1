#! /usr/bin/env pwsh

Add-WindowsCapability -Online -Name OpenSSH.Server
Get-Service -Name sshd | Set-Service -StartupType Automatic
Get-Service -Name ssh-agent | Set-Service -StartupType Automatic
