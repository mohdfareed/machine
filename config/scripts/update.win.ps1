Write-Host "updating windows tools..."

wsl --update

winget upgrade --all --include-unknown
if (Get-Command scoop -ErrorAction SilentlyContinue) {
    scoop update
    scoop update *
    scoop cleanup *
}

Write-Host "windows tools updated successfully"
