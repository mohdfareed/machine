"""Windows feature failures must not prevent attempts at the remaining features."""

import shutil
import subprocess
from pathlib import Path

import pytest


def test_windows_features_report_failures_after_attempting_remaining_features(tmp_path: Path):
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if shell is None:
        pytest.skip("PowerShell is unavailable")
    script = Path(__file__).parents[1] / "config/system/scripts/system.win.ps1"
    harness = tmp_path / "features.ps1"
    harness.write_text(
        r"""
param($ScriptPath)
$ErrorActionPreference = 'Stop'
function Invoke-Admin {
    param([scriptblock]$ScriptBlock)
    & $ScriptBlock
}
function Enable-WindowsOptionalFeature {
    param([switch]$Online, [switch]$NoRestart, $FeatureName, $ErrorAction)
    $global:featureAttempts += $FeatureName
    if ($global:simulateFeatureFailure -and $global:featureAttempts.Count -le 2) {
        throw "simulated failure for $FeatureName"
    }
}
$global:featureAttempts = @()
$global:simulateFeatureFailure = $false
& $ScriptPath
$successfulAttempts = $global:featureAttempts
$global:featureAttempts = @()
$global:simulateFeatureFailure = $true
try {
    & $ScriptPath
    throw 'expected feature setup to fail'
}
catch {
    $expected = "Failed Windows features: $($successfulAttempts[0]), $($successfulAttempts[1])"
    if ($_.Exception.Message -ne $expected) { throw }
}
if ($global:featureAttempts.Count -le 2 -or
    ($global:featureAttempts -join ',') -ne ($successfulAttempts -join ',')) {
    throw 'feature setup stopped early'
}
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(harness), str(script)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.count("failed to enable ") == 2
