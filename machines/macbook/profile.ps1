#!/usr/bin/env pwsh

$env:PATH = "$env:DEV_BIN$([IO.Path]::PathSeparator)$env:PATH"

function Measure-Program {
    <#
    .SYNOPSIS
    Profiles an external command using GNU time.
    .EXAMPLE
    Measure-Program pwsh -NoProfile -Command 'exit'
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, Position = 0)]
        [string]$Command,

        [Parameter(Position = 1, ValueFromRemainingArguments)]
        [string[]]$ArgumentList
    )

    # Resolve the external executable.
    $executable = Get-Command -Name $Command -CommandType Application `
        -ErrorAction Stop | Select-Object -First 1

    # Measure allocated disk space, following symbolic links.
    $diskUsage = & du -Lsk $executable.Path
    if ($LASTEXITCODE -ne 0) {
        throw "Could not measure executable size: $($executable.Path)"
    }

    $sizeKiB = [double](($diskUsage -split '\s+')[0])
    $sizeMiB = '{0:F1}' -f ($sizeKiB / 1024)
    $format = @"
 Elapsed: %es
 Memory:  %M KB peak
 Size:    $sizeMiB MiB
 CPU:     %P |  %Us |  %Ss
"@

    & gtime -f $format -- $executable.Path @ArgumentList
}
