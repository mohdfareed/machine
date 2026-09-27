#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

# Keep Windows containers available; WinGet's default installer flags disable them.
$wingetArguments = @(
    'upgrade',
    '--id', 'Docker.DockerDesktop',
    '--exact', '--source', 'winget', '--scope', 'machine',
    '--accept-source-agreements', '--accept-package-agreements',
    '--override', 'install --quiet --accept-license --backend=wsl-2 --always-run-service'
)

# Upgrade Docker using the same installer options as deployment.
winget @wingetArguments
if ($LASTEXITCODE -notin @(0, 0x8A15002B)) {
    throw "Docker Desktop upgrade failed (exit $LASTEXITCODE)"
}

# Apply upgrade policy even when Docker is already installed and packages are skipped.
winget pin add --id Docker.DockerDesktop --exact --source winget --force --accept-source-agreements
if ($LASTEXITCODE -ne 0) { throw "Could not pin Docker Desktop (exit $LASTEXITCODE)" }
