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
        try {
            & $ScriptBlock @ArgumentList
        }
        catch {
            Write-Host $_.Exception.Message
            exit 1
        }
        if ($LASTEXITCODE) { exit $LASTEXITCODE }
        return
    }

    # A UAC process has its own scope; pass outside values through param()/ArgumentList.
    $arguments = [Management.Automation.PSSerializer]::Serialize($ArgumentList).Replace("'", "''")
    # RunAs cannot redirect stdout; relay text through a shared temporary file.
    $outputPath = [IO.Path]::GetTempFileName()
    $outputLiteral = $outputPath.Replace("'", "''")
    $command = @"
`$ErrorActionPreference = 'Stop'
`$ProgressPreference = 'SilentlyContinue'
`$arguments = [Management.Automation.PSSerializer]::Deserialize('$arguments')
`$script:adminExitCode = 0
`$global:LASTEXITCODE = 0
& {
    try {
        & {
$ScriptBlock
        } @arguments
        `$script:adminExitCode = `$LASTEXITCODE
    }
    catch {
        `$_.Exception.Message
        `$script:adminExitCode = 1
    }
} *>&1 | Out-String -Stream -Width 240 | ForEach-Object {
    if (-not [string]::IsNullOrWhiteSpace(`$_)) {
        [IO.File]::AppendAllText('$outputLiteral', "`$_``r``n", [Text.Encoding]::UTF8)
    }
}
exit `$script:adminExitCode
"@
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($command))

    $reader = $null
    try {
        $reader = [IO.StreamReader]::new(
            [IO.File]::Open($outputPath, 'Open', 'Read', 'ReadWrite'), [Text.Encoding]::UTF8
        )
        Write-Host 'requesting administrator access...'
        try {
            $process = Start-Process `
                -FilePath "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" `
                -Verb RunAs -WindowStyle Hidden `
                -ArgumentList "-NoProfile -ExecutionPolicy Bypass -EncodedCommand $encoded" `
                -PassThru -ErrorAction Stop
        }
        catch {
            Write-Host "Could not obtain administrator access: $($_.Exception.Message)"
            exit 1
        }

        while (-not $process.HasExited) {
            while ($null -ne ($line = $reader.ReadLine())) { Write-Host $line }
            Start-Sleep -Milliseconds 100
        }
        $process.WaitForExit()
        while ($null -ne ($line = $reader.ReadLine())) { Write-Host $line }
        if ($process.ExitCode -ne 0) {
            # The child already printed its error; preserve failure without another error record.
            exit $process.ExitCode
        }
    }
    finally {
        if ($reader) { $reader.Dispose() }
        Remove-Item -LiteralPath $outputPath -Force -ErrorAction SilentlyContinue
    }
}

Export-ModuleMember -Function Invoke-Admin
