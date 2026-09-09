#! /usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

Write-Host "installing OpenSSH..."
Invoke-Admin {
    Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
    Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
    Get-Service -Name sshd | Set-Service -StartupType Automatic
    Get-Service -Name ssh-agent | Set-Service -StartupType Automatic
}

Write-Host 'making PowerShell profile links trusted for SSH...'
Invoke-Admin {
    # RedirectionGuard in SSH sessions rejects links created without elevation.
    param($profileDirectory)
    foreach ($name in 'profile.ps1', 'aliases.ps1', 'profile.local.ps1') {
        $path = Join-Path $profileDirectory $name
        $link = Get-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
        if ($null -eq $link -or $link.LinkType -ne 'SymbolicLink' -or $link.PSIsContainer) {
            continue
        }

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
} -ArgumentList (Join-Path $HOME 'Documents\PowerShell')

# Configure OpenSSH to use the PowerShell MSIX executable as the default shell.
# This is the new windows default distribution for PowerShell.
$powerShellPackage = Get-AppxPackage -Name Microsoft.PowerShell
if (-not $powerShellPackage) {
    throw 'PowerShell MSIX is not installed for the current user.'
}

# Use the real executable, not the app alias; rediscover its path after MSIX updates.
# NOTE: This breaks across MSIX updates. Rerun `mc apply ssh-server` to fix.
$defaultShell = Join-Path $powerShellPackage.InstallLocation 'pwsh.exe'
if (-not (Test-Path -LiteralPath $defaultShell -PathType Leaf)) {
    throw "PowerShell executable not found: $defaultShell"
}

Write-Host "configuring OpenSSH PowerShell..."
Invoke-Admin {
    # Set the default shell for OpenSSH to PowerShell.
    # Windows default distribution is now MSIX.
    param($defaultShell)
    New-ItemProperty `
        -Path "HKLM:\SOFTWARE\OpenSSH" `
        -Name DefaultShell `
        -Value $defaultShell `
        -PropertyType String `
        -Force | Out-Null

    # Windows OpenSSH overrides authorized_keys for Administrators to a separate
    # file (administrators_authorized_keys), breaking standard pubkey auth.
    $sshdConfig = "$env:ProgramData\ssh\sshd_config"
    (Get-Content $sshdConfig) -replace '^(Match Group administrators)', '#$1' `
        -replace '^(\s*AuthorizedKeysFile __PROGRAMDATA__)', '#$1' |

    Set-Content $sshdConfig
    Restart-Service sshd
} -ArgumentList $defaultShell
