#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

foreach ($name in 'MC_HOMELAB_STORAGE_DIR', 'MC_HOMELAB_MEDIA_DIR') {
    if ([string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($name))) {
        throw "Environment variable is required: $name"
    }
}

$storageDir = $env:MC_HOMELAB_STORAGE_DIR
$mediaDir = $env:MC_HOMELAB_MEDIA_DIR

New-Item -ItemType Directory -Path $storageDir -Force | Out-Null
New-Item -ItemType Directory -Path $mediaDir -Force | Out-Null

New-Item -ItemType Directory -Path (Join-Path $mediaDir 'movies') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $mediaDir 'series') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $mediaDir 'anime') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $mediaDir 'downloads') -Force | Out-Null
