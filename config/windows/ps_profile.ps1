# Environment: Windows
# =============================================================================

# Global environment variables
$profilePath = (Resolve-Path $PROFILE).Path
$configPath = (Get-Item $profilePath).Directory.Parent.Parent.Parent.FullName
$psProfilePath = Join-Path -Path $configPath -ChildPath "config/ps_profile.ps1"
. $psProfilePath

Remove-Variable profilePath
Remove-Variable configPath
Remove-Variable psProfilePath

# Machine specific environment variables
