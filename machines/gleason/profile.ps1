#!/usr/bin/env pwsh

# dev bin
Get-ChildItem -Path $env:DEV_BIN -Filter *.psm1 | ForEach-Object {
    Import-Module $_.FullName
}
$env:Path += ";$env:DEV_BIN"

# msbuild
$env:Path += ";C:\Program Files\Microsoft Visual Studio\18\Professional\MSBuild\Current\Bin"
