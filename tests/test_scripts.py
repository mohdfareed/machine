"""Sequential script execution and Windows setup behavior."""

import os
import runpy
import shutil
import subprocess
import sys
from pathlib import Path

import platformdirs
import pytest
from app import env as machine_env
from app import machine as machine_loader
from app import shell
from app.models import Platform
from app.ops import scripts as machine_scripts


@pytest.mark.parametrize("platform", [Platform.WIN, Platform.MAC, Platform.WSL])
def test_script_selection_excludes_shell_on_windows(monkeypatch, platform):
    monkeypatch.setattr(machine_env, "PLATFORM", platform)
    names = ["setup.py", "setup.ps1", "setup.sh", "setup.win.sh", "_helper.py", "setup.txt"]
    scripts = [Path(name) for name in names]
    expected = scripts[:2] if platform == Platform.WIN else scripts[:3]
    assert machine_loader._resolve_scripts(scripts) == expected


def test_powershell_mappings_follow_redirected_documents(monkeypatch, tmp_path):
    documents = tmp_path / "Redirected Documents"
    monkeypatch.setattr(machine_env, "PLATFORM", Platform.WIN)
    monkeypatch.setattr(platformdirs, "user_documents_path", lambda: documents)
    path = Path(__file__).parents[1] / "config/terminal/shell/module.py"
    module = runpy.run_path(str(path))["module"]

    mappings = [file for file in [*module.files, *module.overrides] if file.source.suffix == ".ps1"]
    assert mappings
    assert all(file.target.parent == documents / "PowerShell" for file in mappings)


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
        assert cmd[0] == sys.executable
        name = Path(cmd[-1]).name
        events.append(name)
        if name == failed_script:
            raise RuntimeError("script failed")

    monkeypatch.setattr(machine_scripts, "run", run)
    with pytest.raises(RuntimeError, match="script failed"):
        machine_scripts.run_scripts(scripts, env=dict(os.environ), dry_run=False)

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
            scripts,
            env={**os.environ, "SCRIPT_MARKER": str(marker)},
            dry_run=False,
        )

    assert marker.read_text().splitlines() == ["ran"] * 4


@pytest.mark.parametrize("shebang", ["#!/bin/sh", "#!/bin/bash"])
def test_script_preview_preserves_permissions(tmp_path: Path, monkeypatch, shebang) -> None:
    script = tmp_path / "init_preview.sh"
    script.write_text(f"{shebang}\nexit 1\n")
    script.chmod(0o600)
    mode = script.stat().st_mode
    monkeypatch.setattr(shell.shutil, "which", lambda *a, **kw: None)
    machine_scripts.run_scripts([script], env=dict(os.environ), dry_run=True)

    assert script.stat().st_mode == mode


@pytest.mark.skipif(sys.platform == "win32", reason="Unix executable permissions")
def test_script_execution_does_not_repair_permissions(tmp_path):
    script = tmp_path / "not-executable.sh"
    script.write_text("#!/bin/sh\nexit 0\n")
    script.chmod(0o600)
    with pytest.raises(PermissionError):
        machine_scripts.run_scripts([script], env={}, dry_run=False)
    assert script.stat().st_mode & 0o777 == 0o600


@pytest.mark.skipif(sys.platform == "win32", reason="Unix script execution")
def test_scripts_preserve_prepared_environment_without_loading_startup(tmp_path, monkeypatch):
    # Make user startup conflict with the environment prepared for this invocation.
    (tmp_path / ".profile").write_text(
        "export MC_ID=other MC_VALUE=committed PATH=/committed/bin\n"
    )
    activation = tmp_path / "environment.sh"
    activation.write_text("")
    monkeypatch.setattr(shell, "_ENVIRONMENT_SCRIPT", activation)
    selected_path = "/selected/bin"
    environment = {
        "HOME": str(tmp_path),
        "MC_ID": "selected",
        "MC_VALUE": "private",
        "PATH": selected_path,
    }

    # The OS executes the declared shebang; the runner does not reinterpret it.
    script = tmp_path / "inspect script.sh"
    result = tmp_path / "result.txt"
    script.write_text('#!/bin/sh\nprintf "%s\\n" "$MC_ID|$MC_VALUE|$PATH" > "$RESULT"\n')
    script.chmod(0o755)
    machine_scripts.run_scripts([script], env={**environment, "RESULT": str(result)}, dry_run=False)
    assert result.read_text().strip() == f"selected|private|{selected_path}"


def test_powershell_preview_does_not_prepare_an_unavailable_interpreter(tmp_path, monkeypatch):
    script = tmp_path / "setup.ps1"
    script.write_text("throw 'preview executed'\n")
    monkeypatch.setattr(shell.shutil, "which", lambda *a, **kw: None)
    monkeypatch.setattr(
        shell, "process_env", lambda *a: pytest.fail("preview prepared environment")
    )

    machine_scripts.run_scripts([script], env={}, dry_run=True)


@pytest.mark.parametrize("exit_code", [0, 7])
def test_homelab_elevation_failure_stops_before_user_package_setup(tmp_path, exit_code):
    powershell = shutil.which("pwsh") or shutil.which("powershell.exe")
    if powershell is None:
        pytest.skip("PowerShell is unavailable")
    script = Path(__file__).parents[1] / "config/homelab/scripts/init_system.win.ps1"
    harness = tmp_path / "elevation.ps1"
    harness.write_text(
        r"""
param($ScriptPath, [int]$ExitCode)
$ErrorActionPreference = 'Stop'
function Start-Process {
    param($FilePath, $ArgumentList, $Verb, [switch]$Wait, [switch]$PassThru)
    if ($Verb -ne 'RunAs' -or -not $Wait -or -not $PassThru -or
        $ArgumentList[-1] -ne '-Admin' -or $ArgumentList[-2] -ne "`"$ScriptPath`"") {
        throw 'unexpected elevation arguments'
    }
    [pscustomobject]@{ ExitCode = $ExitCode }
}
function winget {
    Write-Output 'user-package-setup'
    $global:LASTEXITCODE = 0
}
& $ScriptPath
exit $LASTEXITCODE
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(harness),
            str(script),
            str(exit_code),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == exit_code, result.stdout + result.stderr
    assert ("user-package-setup" in result.stdout) == (exit_code == 0)


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
function Enable-WindowsOptionalFeature {
    param([switch]$Online, [switch]$NoRestart, $FeatureName, $ErrorAction)
    $global:featureAttempts += $FeatureName
    if ($global:simulateFeatureFailure -and $global:featureAttempts.Count -le 2) {
        throw "simulated failure for $FeatureName"
    }
}
$global:featureAttempts = @()
$global:simulateFeatureFailure = $false
& $ScriptPath -Admin
$successfulAttempts = $global:featureAttempts
$global:featureAttempts = @()
$global:simulateFeatureFailure = $true
try {
    & $ScriptPath -Admin
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
