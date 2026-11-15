#!/usr/bin/env pwsh

# dev bin
Get-ChildItem -Path $env:DEV_BIN -Filter *.psm1 | ForEach-Object {
    Import-Module $_.FullName
}
$env:PATH += [IO.Path]::PathSeparator + $env:DEV_BIN

# msbuild
$env:PATH += [IO.Path]::PathSeparator + `
"C:\Program Files\Microsoft Visual Studio\18\Professional\MSBuild\Current\Bin"
