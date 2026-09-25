#!/usr/bin/env pwsh
#Requires -Version 7.4
$ErrorActionPreference = 'Stop'
$root = Join-Path $PSScriptRoot '../..'

# Parse scripts without executing them.
$failed = $false
foreach ($folder in 'app', 'config', 'machines', 'scripts') {
    foreach ($script in Get-ChildItem (Join-Path $root $folder) -Recurse -File) {
        if ($script.Extension -notin '.ps1', '.psm1') { continue }
        $tokens = $null
        $errors = $null
        [Management.Automation.Language.Parser]::ParseFile(
            $script.FullName, [ref]$tokens, [ref]$errors
        ) > $null
        foreach ($parseError in $errors) {
            Write-Error "$($script.FullName): $parseError" -ErrorAction Continue
            $failed = $true
        }
    }
}
if ($failed) { exit 1 }
