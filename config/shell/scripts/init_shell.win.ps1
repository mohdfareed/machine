#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

# Keep Scoop's launchers usable over SSH without version-directory junctions.
scoop config no_junction true
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Carapace is distributed through Scoop's extras bucket.
$buckets = scoop bucket list
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if ($buckets.Name -contains 'extras') { return }
scoop bucket add extras
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
