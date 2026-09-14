#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

if (-not $env:MC_HOMELAB_DIR) {
    throw 'MC_HOMELAB_DIR is required.'
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'docker not found'
}

$homelabDir = $env:MC_HOMELAB_DIR
$dockerDirectories = @(
    (Join-Path $env:MC_HOME 'config\homelab\docker')
    (Join-Path $env:MC_MACHINE 'docker')
)

# Wait for Docker Desktop to start.
Write-Host 'waiting for docker daemon...'
$dockerReady = $false
foreach ($attempt in 1..30) {
    docker info *> $null
    if ($LASTEXITCODE -eq 0) {
        $dockerReady = $true
        break
    }
    Start-Sleep -Seconds 2
}
if (-not $dockerReady) {
    throw 'docker daemon not available'
}

# Link homelab service directories while preserving existing runtime data.
New-Item -ItemType Directory -Path $homelabDir -Force | Out-Null
function Set-ServiceLink {
    param([IO.DirectoryInfo]$ServiceDirectory)

    $link = Join-Path $homelabDir $ServiceDirectory.Name
    $item = Get-Item -LiteralPath $link -Force -ErrorAction SilentlyContinue
    if ($item -and $item.LinkType) {
        $target = @($item.Target)[0]
        if (-not [IO.Path]::IsPathRooted($target)) {
            $target = Join-Path $item.Parent.FullName $target
        }
        if ([IO.Path]::GetFullPath($target) -eq $ServiceDirectory.FullName) {
            return
        }
        Remove-Item -LiteralPath $link -Force
    }
    elseif ($item) {
        foreach ($runtime in 'data', 'logs') {
            $source = Join-Path $link $runtime
            $destination = Join-Path $ServiceDirectory.FullName $runtime
            if ((Test-Path -LiteralPath $source) -and -not (Test-Path -LiteralPath $destination)) {
                Write-Host "migrating $($ServiceDirectory.Name)/$runtime → repo..."
                Move-Item -LiteralPath $source -Destination $destination
            }
        }
        Remove-Item -LiteralPath $link -Recurse -Force
    }

    New-Item -ItemType Junction -Path $link -Target $ServiceDirectory.FullName | Out-Null
}

foreach ($dockerDirectory in $dockerDirectories) {
    if (-not (Test-Path -LiteralPath $dockerDirectory -PathType Container)) {
        continue
    }
    foreach ($serviceDirectory in Get-ChildItem -LiteralPath $dockerDirectory -Directory) {
        Set-ServiceLink $serviceDirectory
    }
}

# =============================================================================
# MARK: Deploy
# =============================================================================

# Deploy each Compose project from its repository directory.
foreach ($dockerDirectory in $dockerDirectories) {
    if (-not (Test-Path -LiteralPath $dockerDirectory -PathType Container)) {
        continue
    }
    foreach ($serviceDirectory in Get-ChildItem -LiteralPath $dockerDirectory -Directory) {
        if (-not (Test-Path -LiteralPath (Join-Path $serviceDirectory 'compose.yaml'))) {
            continue
        }

        Write-Host "deploying $($serviceDirectory.Name)..."
        Push-Location $serviceDirectory
        try {
            docker compose pull --ignore-pull-failures
            if ($LASTEXITCODE -ne 0) {
                throw "docker compose pull failed for $($serviceDirectory.Name)"
            }
            docker compose up -d --build --remove-orphans
            if ($LASTEXITCODE -ne 0) {
                throw "docker compose up failed for $($serviceDirectory.Name)"
            }
        }
        finally {
            Pop-Location
        }
    }
}

Write-Host 'all services deployed.'
