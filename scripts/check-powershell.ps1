$ErrorActionPreference = "Stop"

# Parse each script without executing it.
$failed = $false
foreach ($path in $args) {
    $tokens = $null
    $errors = $null
    [Management.Automation.Language.Parser]::ParseFile(
        $path,
        [ref]$tokens,
        [ref]$errors
    ) > $null

    foreach ($parseError in $errors) {
        Write-Error "${path}: $parseError" -ErrorAction Continue
        $failed = $true
    }
}

if ($failed) { exit 1 }
