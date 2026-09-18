#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

# Install interactive modules.
Install-Module -Name PSFzf
Install-Module -Name posh-git

# Create trusted profile links for Windows SSH sessions.
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    return
}

# Target PowerShell 7 even when setup runs in Windows PowerShell.
$documents = [Environment]::GetFolderPath('MyDocuments', 'DoNotVerify')
if ([string]::IsNullOrWhiteSpace($documents)) {
    throw 'Windows Documents directory is unavailable.'
}
$profileDirectory = Join-Path $documents 'PowerShell'
if (-not (Test-Path -LiteralPath $profileDirectory -PathType Container)) {
    return
}

Write-Host 'making PowerShell profile links trusted for SSH...'
Invoke-Admin {
    # RedirectionGuard in SSH sessions rejects links created without elevation.
    param($profileDirectory)
    foreach ($link in Get-ChildItem -LiteralPath $profileDirectory -Filter '*.ps1' -File) {
        if ($link.LinkType -ne 'SymbolicLink') {
            continue
        }

        $path = $link.FullName
        $target = @($link.Target)[0]
        if (-not [IO.Path]::IsPathRooted($target)) {
            $target = Join-Path $profileDirectory $target
        }
        if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
            throw "Profile link target is missing: $target"
        }

        # Preserve the original link until its elevated replacement is created.
        $backup = "$path.$([guid]::NewGuid().ToString('N')).backup"
        Move-Item -LiteralPath $path -Destination $backup
        try {
            New-Item -ItemType SymbolicLink -Path $path -Target $target | Out-Null
        }
        catch {
            Move-Item -LiteralPath $backup -Destination $path
            throw
        }
        Remove-Item -LiteralPath $backup -Force
    }
} -ArgumentList $profileDirectory
