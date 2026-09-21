#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

# Upgrade Docker using the same installer options as deployment.
& "$PSScriptRoot/docker.win.ps1" -Upgrade
