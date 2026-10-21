#!/usr/bin/env pwsh

function Wake-PC {
    Invoke-RestMethod -Method Post -Uri 'https://homelab.tail2a477.ts.net/actions/wake-pc' -Headers @{
        Origin = 'https://dashboard.tail2a477.ts.net'
        'X-Wake-PC' = '1'
    } -TimeoutSec 10 -MaximumRedirection 0 -ErrorAction Stop |
        Select-Object -ExpandProperty message
}
