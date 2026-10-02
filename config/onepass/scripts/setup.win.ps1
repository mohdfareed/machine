#!/usr/bin/env pwsh
param([switch]$Admin)
$ErrorActionPreference = 'Stop'

# Release the Windows agent pipe only when 1Password is selected.
$agent = Get-Service -ErrorAction Stop | Where-Object Name -eq 'ssh-agent'
if (-not $agent -or ($agent.Status -eq 'Stopped' -and $agent.StartType -eq 'Disabled')) {
    if ($Admin) { Read-Host 'Press Enter to exit' }
    return
}

if ($Admin) {
    $exitCode = 0
    try {
        Write-Host 'disabling the Windows OpenSSH authentication agent for 1Password...'
        if ($agent.StartType -ne 'Disabled') {
            Set-Service -Name ssh-agent -StartupType Disabled
        }
        if ($agent.Status -ne 'Stopped') {
            Stop-Service -Name ssh-agent
            (Get-Service -Name ssh-agent).WaitForStatus('Stopped', [TimeSpan]::FromSeconds(30))
        }
    }
    catch {
        Write-Error "Could not release the Windows SSH agent for 1Password: $_" -ErrorAction Continue
        $exitCode = 1
    }
    finally {
        Read-Host 'Press Enter to exit'
    }
    exit $exitCode
}

# Elevate only the service change; deployment keeps the invoking user's context.
$arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"", '-Admin')
$powershell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$process = Start-Process -FilePath $powershell -ArgumentList $arguments `
    -Verb RunAs -Wait -PassThru
if ($process.ExitCode -ne 0) {
    throw 'Windows SSH agent setup failed. Rerun mc deploy and approve the service-change elevation.'
}
