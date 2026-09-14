"""Sequential script execution and Windows setup behavior."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from app.ops import scripts as machine_scripts


@pytest.mark.parametrize("failed_script", ["init_failed.py", "setup.py"])
def test_scripts_stop_on_first_failure_without_interpreting_prefixes(
    tmp_path: Path, monkeypatch, failed_script: str
) -> None:
    events = []
    scripts = [tmp_path / name for name in ("init_first.py", failed_script, "last.py")]
    for script in scripts:
        script.write_text("pass\n")

    def run(cmd, *, env, dry_run, check, powershell):
        assert not powershell
        assert check is True
        assert dry_run is False
        name = Path(cmd[-1]).name
        events.append(name)
        if name == failed_script:
            raise RuntimeError("script failed")

    monkeypatch.setattr(machine_scripts, "run", run)
    with pytest.raises(RuntimeError, match="script failed"):
        machine_scripts.run_scripts(
            [str(script) for script in scripts], env=dict(os.environ), dry_run=False
        )

    assert events == ["init_first.py", failed_script]


def test_scripts_run_each_time_with_spaced_paths(tmp_path: Path) -> None:
    directory = tmp_path / "script directory"
    directory.mkdir()
    marker = tmp_path / "runs.txt"
    scripts = [directory / name for name in ("once_setup.py", "watch_setup.py")]
    for script in scripts:
        script.write_text(
            "import os\n"
            "with open(os.environ['SCRIPT_MARKER'], 'a') as marker:\n"
            "    marker.write('ran\\n')\n"
        )

    for _ in range(2):
        machine_scripts.run_scripts(
            [str(script) for script in scripts],
            env={**os.environ, "SCRIPT_MARKER": str(marker)},
            dry_run=False,
        )

    assert marker.read_text().splitlines() == ["ran"] * 4


def test_script_preview_preserves_permissions(tmp_path: Path) -> None:
    script = tmp_path / "init_preview.sh"
    script.write_text("#!/bin/sh\nexit 1\n")
    script.chmod(0o600)
    mode = script.stat().st_mode
    machine_scripts.run_scripts([str(script)], env=dict(os.environ), dry_run=True)

    assert script.stat().st_mode == mode


def test_powershell_preview_does_not_prepare_an_unavailable_interpreter(tmp_path, monkeypatch):
    from app import shell

    script = tmp_path / "setup.ps1"
    script.write_text("throw 'preview executed'\n")
    monkeypatch.setattr(shell.shutil, "which", lambda *a, **kw: None)
    monkeypatch.setattr(
        shell,
        "prepare_powershell_env",
        lambda *a: pytest.fail("preview queried PowerShell"),
    )

    machine_scripts.run_scripts([str(script)], env={}, dry_run=True)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows elevation helper")
@pytest.mark.parametrize("already_admin", [False, True])
@pytest.mark.parametrize("mode,exit_code", [("success", 0), ("throw", 1), ("native", 7)])
def test_admin_output_and_failure_status(tmp_path: Path, already_admin, mode, exit_code):
    shell = shutil.which("powershell.exe")
    if shell is None:
        pytest.skip("Windows PowerShell is unavailable")
    source = Path(__file__).parents[1] / "app/scripts/MachineAdmin/MachineAdmin.psm1"
    module = tmp_path / "MachineAdmin.psm1"
    # Exercise either branch without elevation or any machine changes.
    module.write_text(
        source.read_text().replace(
            "if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))",
            "if ($true)" if already_admin else "if ($false)",
        ),
        encoding="utf-8",
    )
    script = tmp_path / "relay.ps1"
    script.write_text(
        "param($ModulePath, $Mode)\n"
        "$ErrorActionPreference = 'Stop'\n"
        "$module = Import-Module $ModulePath -PassThru\n"
        + r"""
& $module {
    function script:Start-Process {
        param($FilePath, $Verb, $WindowStyle, $ArgumentList, [switch]$PassThru, $ErrorAction)
        if ($Verb -ne 'RunAs' -or $WindowStyle -ne 'Hidden') { throw 'unexpected launch options' }
        Microsoft.PowerShell.Management\Start-Process -FilePath $FilePath `
            -WindowStyle Hidden -ArgumentList $ArgumentList -PassThru -ErrorAction Stop
    }
}
Invoke-Admin {
    param($mode, $message)
    Write-Host $message
    Write-Output 'relay-output'
    Write-Output ''
    Write-Output '   '
    Write-Warning 'relay-warning'
    Write-Verbose 'relay-verbose' -Verbose
    if ($mode -eq 'throw') { throw 'relay-error' }
    if ($mode -eq 'native') { cmd.exe /c 'echo native-output & exit 7' }
} -ArgumentList $Mode, "relay-host 'quoted'"
Write-Host 'after-admin'
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            shell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            str(module),
            mode,
        ],
        env={**os.environ, "TEMP": str(tmp_path), "TMP": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = result.stdout + result.stderr
    assert result.returncode == exit_code, output
    assert ("after-admin" in output) == (exit_code == 0), output
    for message in ("relay-host 'quoted'", "relay-output", "relay-warning", "relay-verbose"):
        assert message in output, output
    if mode == "throw":
        assert output.count("relay-error") == 1, output
    if mode == "native":
        assert "native-output" in output
    if not already_admin:
        assert all(line.strip() for line in output.splitlines()), output
    assert "CategoryInfo" not in output
    assert "Admin block failed" not in output
    assert not list(tmp_path.glob("*.tmp")), "relay temporary file was not cleaned up"


def test_windows_features_report_failures_after_attempting_remaining_features(tmp_path: Path):
    shell = shutil.which("pwsh") or shutil.which("pwsh-preview") or shutil.which("powershell")
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
