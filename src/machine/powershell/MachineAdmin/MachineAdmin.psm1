function Invoke-Admin {
    param(
        [Parameter(Mandatory, Position = 0)]
        [scriptblock]$ScriptBlock,
        [object[]]$ArgumentList = @()
    )

    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        $ErrorActionPreference = 'Stop'
        $global:LASTEXITCODE = 0
        & $ScriptBlock @ArgumentList
        if ($LASTEXITCODE) { throw "Admin block failed (exit $LASTEXITCODE)." }
        return
    }

    # A UAC process has its own scope; pass outside values through param()/ArgumentList.
    $arguments = [Management.Automation.PSSerializer]::Serialize($ArgumentList).Replace("'", "''")
    $command = @"
`$ErrorActionPreference = 'Stop'
`$arguments = [Management.Automation.PSSerializer]::Deserialize('$arguments')
& {
$ScriptBlock
} @arguments
exit `$LASTEXITCODE
"@
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($command))

    Write-Host 'requesting administrator access...'
    try {
        $process = Start-Process `
            -FilePath "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" `
            -Verb RunAs `
            -ArgumentList "-NoProfile -ExecutionPolicy Bypass -EncodedCommand $encoded" `
            -Wait -PassThru -ErrorAction Stop
    }
    catch {
        throw "Could not obtain administrator access: $($_.Exception.Message)"
    }
    if ($process.ExitCode -ne 0) {
        throw "Admin block failed (exit $($process.ExitCode))."
    }
}

Export-ModuleMember -Function Invoke-Admin
