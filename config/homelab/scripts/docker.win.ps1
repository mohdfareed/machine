#!/usr/bin/env pwsh
param([switch]$Upgrade)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

# Select installation or an explicit upgrade, accepting only its expected no-op.
$operation = 'install'
$noOpCode = 0x8A150061 # Package already installed.
if ($Upgrade) {
    $operation = 'upgrade'
    $noOpCode = 0x8A15002B # No applicable update.
}

# Keep Windows containers available; WinGet's default installer flags disable them.
$wingetArguments = @(
    $operation,
    '--id', 'Docker.DockerDesktop',
    '--exact', '--source', 'winget', '--scope', 'machine',
    '--accept-source-agreements', '--accept-package-agreements',
    '--override', 'install --quiet --accept-license --backend=wsl-2 --always-run-service'
)
if (-not $Upgrade) { $wingetArguments += '--no-upgrade' }

winget @wingetArguments
if ($LASTEXITCODE -notin @(0, $noOpCode)) {
    throw "Docker Desktop $operation failed (exit $LASTEXITCODE)"
}
