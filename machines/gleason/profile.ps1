#!/usr/bin/env pwsh

# dev bin
Get-ChildItem -Path $DEV_BIN -Filter *.psm1 | ForEach-Object {
    Import-Module $_.FullName
}
$env:Path += ";$DEV_BIN"
