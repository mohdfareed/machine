#!/usr/bin/env pwsh
#Requires -Version 7.0
$ErrorActionPreference = 'Stop'

# Upgrade the interactive modules already installed for PowerShell 7.
Update-Module -Name PSFzf -Force
Update-Module -Name PSCompletions -Force
Update-Help -ErrorAction Continue
psc update
