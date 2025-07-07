#!/usr/bin/env pwsh

Write-Host "updating windows tools..."

Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

winget upgrade --all --include-unknown
if (Get-Command scoop -ErrorAction SilentlyContinue) {
    scoop update
    scoop update *
    scoop cleanup *
}

Write-Host "windows tools updated successfully"
