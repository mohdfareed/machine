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

        # Parse script file contents.
        $ast = [Management.Automation.Language.Parser]::ParseFile(
            $script.FullName, [ref]$tokens, [ref]$errors
        )

        # Report errors found.
        foreach ($parseError in $errors) {
            Write-Error "$($script.FullName): $parseError" -ErrorAction Continue
            $failed = $true
        }

        # Misplaced param blocks parse as commands rather than syntax errors.
        # Catch and handle manually.
        foreach ($command in $ast.FindAll({
            param($node)
            $node -is [Management.Automation.Language.CommandAst] -and
                $node.GetCommandName() -eq 'param'
        }, $true)) {
            Write-Error "$($script.FullName):$($command.Extent.StartLineNumber): misplaced param block" -ErrorAction Continue
            $failed = $true
        }
    }
}

if ($failed) { exit 1 }
