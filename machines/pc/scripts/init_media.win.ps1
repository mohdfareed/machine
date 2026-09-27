#!/usr/bin/env pwsh
param(
    [switch]$Admin,
    [string]$MediaDir,
    [string]$Account
)
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

# Capture the owner before UAC can switch to a different administrator account.
if (-not $Admin) {
    $MediaDir = $env:MC_HOMELAB_MEDIA_DIR
    $Account = [Security.Principal.WindowsIdentity]::GetCurrent().Name
}
if ([string]::IsNullOrWhiteSpace($MediaDir) -or $MediaDir.Contains('"') -or
    $MediaDir -notmatch '^[A-Za-z]:[\\/]') {
    throw 'MC_HOMELAB_MEDIA_DIR must be an absolute local drive path'
}
if ([string]::IsNullOrWhiteSpace($Account) -or $Account.Contains('"')) {
    throw 'A Windows owner account is required'
}
$MediaDir = [IO.Path]::GetFullPath($MediaDir).TrimEnd('\', '/')
$parent = Split-Path -Path $MediaDir -Parent
if (-not $parent -or -not (Test-Path -LiteralPath $parent -PathType Container)) {
    throw "Media parent directory does not exist: $parent"
}

# Pass only explicit, non-secret settings to the visible administrator process.
if (-not $Admin) {
    $arguments = @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"", '-Admin',
        '-MediaDir', "`"$MediaDir`"", '-Account', "`"$Account`""
    )
    $process = Start-Process -FilePath (Get-Process -Id $PID).Path -ArgumentList $arguments `
        -Verb RunAs -Wait -PassThru
    exit $process.ExitCode
}

# Start native SMB and refuse to repoint an existing share.
$server = Get-Service -Name LanmanServer
if ($server.StartType -ne 'Automatic') { Set-Service -Name LanmanServer -StartupType Automatic }
if ($server.Status -ne 'Running') { Start-Service -Name LanmanServer }
$share = Get-SmbShare | Where-Object Name -eq 'Media'
if ($share -and [IO.Path]::GetFullPath($share.Path).TrimEnd('\', '/') -ine $MediaDir) {
    throw "SMB share Media already points to a different path: $($share.Path)"
}

# Preserve media and existing ACLs; add inheritable Modify rights for its owner.
Write-Host 'configuring media storage and sharing...'
$owner = [Security.Principal.NTAccount]::new($Account)
$sid = $owner.Translate([Security.Principal.SecurityIdentifier]).Value
if (-not (Test-Path -LiteralPath $MediaDir -PathType Container)) {
    New-Item -ItemType Directory -Path $MediaDir | Out-Null
}
icacls $MediaDir /grant "*${sid}:(OI)(CI)M"
if ($LASTEXITCODE -ne 0) { throw "Could not grant media access to $Account" }
foreach ($name in 'movies', 'series', 'anime', 'downloads') {
    $directory = Join-Path $MediaDir $name
    if (Test-Path -LiteralPath $directory -PathType Container) { continue }
    New-Item -ItemType Directory -Path $directory | Out-Null
}
if ($share) {
    Grant-SmbShareAccess -Name Media -AccountName $Account -AccessRight Change -Force | Out-Null
}
if (-not $share) {
    New-SmbShare -Name Media -Path $MediaDir -ChangeAccess $Account | Out-Null
}

# Allow SMB only on Private networks from the local subnet, not Public networks.
$ruleName = 'MC-Media-SMB'
$rule = Get-NetFirewallRule | Where-Object Name -eq $ruleName
$settings = @{
    DisplayName = 'Media SMB (Private LAN)'
    Enabled = 'True'
    Direction = 'Inbound'
    Action = 'Allow'
    Profile = 'Private'
    Protocol = 'TCP'
    LocalPort = 445
    RemoteAddress = 'LocalSubnet'
    EdgeTraversalPolicy = 'Block'
}
if ($rule) {
    Set-NetFirewallRule -Name $ruleName @settings
}
if (-not $rule) {
    New-NetFirewallRule -Name $ruleName @settings | Out-Null
}

# Keep storage available on AC without requiring automatic sign-in.
Write-Host 'configuring power management...'
powercfg /change standby-timeout-ac 0
if ($LASTEXITCODE -ne 0) { throw 'Could not disable automatic sleep' }
powercfg /change hibernate-timeout-ac 0
if ($LASTEXITCODE -ne 0) { throw 'Could not disable automatic hibernation' }
