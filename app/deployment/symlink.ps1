#Requires -RunAsAdministrator
param(
    [Parameter(Mandatory)][string]$Source,
    [Parameter(Mandatory)][string]$Target,
    [Parameter(Mandatory)][string]$Owner
)
$ErrorActionPreference = 'Stop'

New-Item -ItemType SymbolicLink -Path $Target -Target $Source | Out-Null
icacls $Target /setowner $Owner /L
exit $LASTEXITCODE
