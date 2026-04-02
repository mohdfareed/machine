#!/usr/bin/env pwsh

# dev bin
Get-ChildItem -Path $DEV_BIN -Filter *.psm1 | ForEach-Object {
    Import-Module $_.FullName
}
$env:Path += ";$DEV_BIN"

# msbuild
$env:Path += ";C:\Program Files\Microsoft Visual Studio\18\Professional\MSBuild\Current\Bin"
