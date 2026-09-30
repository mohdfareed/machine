"""Sequential script execution and Windows setup behavior."""

import os
import runpy
import shutil
import subprocess
import sys
from pathlib import Path

import platformdirs
import pytest
from app.config import loader as machine_loader
from app.config.models import Platform
from app.deployment import scripts as machine_scripts
from app.runtime import env as machine_env
from app.runtime import shell


@pytest.mark.skipif(sys.platform == "win32", reason="Unix bootstrap")
@pytest.mark.parametrize("kernel", ["6.8.0-generic", "4.4.0-19041-Microsoft"])
def test_bootstrap_rejects_unsupported_linux_before_setup(tmp_path, kernel):
    uname = tmp_path / "uname"
    uname.write_text(
        '#!/bin/sh\ncase "$1" in\n'
        "  -s) echo Linux ;;\n"
        "  -m) echo x86_64 ;;\n"
        f'  -r) echo "{kernel}" ;;\n'
        "  *) exit 99 ;;\nesac\n"
    )
    uname.chmod(0o755)
    result = subprocess.run(
        ["/bin/sh", str(machine_env.ROOT / "scripts" / "bootstrap.sh")],
        env={**os.environ, "PATH": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 1
    assert "Unsupported host" in result.stderr
    assert not result.stdout


@pytest.mark.parametrize("platform", [Platform.WIN, Platform.MAC])
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
    path = Path(__file__).parents[1] / "config/shell/module.py"
    module = runpy.run_path(str(path))["module"]

    mappings = [file for file in [*module.files, *module.overrides] if file.source.suffix == ".ps1"]
    assert mappings
    assert all(file.target.parent == documents / "PowerShell" for file in mappings)


def test_scripts_preserve_order_and_stop_on_first_failure(tmp_path: Path) -> None:
    marker = tmp_path / "runs.txt"
    scripts = [tmp_path / name for name in ("setup.py", "init_failed.py", "last.py")]
    for script in scripts:
        script.write_text(
            "import os, sys\n"
            "with open(os.environ['SCRIPT_MARKER'], 'a') as marker:\n"
            f"    marker.write({script.name!r} + '\\n')\n"
            f"sys.exit({7 if script.name == 'init_failed.py' else 0})\n"
        )

    with pytest.raises(subprocess.CalledProcessError) as failure:
        machine_scripts.run_scripts(scripts, env={"SCRIPT_MARKER": str(marker)}, dry_run=False)

    assert failure.value.returncode == 7
    assert marker.read_text().splitlines() == ["setup.py", "init_failed.py"]


def test_scripts_run_each_time_with_spaced_paths(tmp_path: Path) -> None:
    directory = tmp_path / "script directory"
    directory.mkdir()
    marker = tmp_path / "runs.txt"
    scripts = [directory / name for name in ("once_setup.py", "watch_setup.py")]
    for script in scripts:
        script.write_text(
            "import os\n"
            "with open(os.environ['SCRIPT_MARKER'], 'a') as marker:\n"
            f"    marker.write({script.name!r} + '\\n')\n"
        )

    for _ in range(2):
        machine_scripts.run_scripts(
            scripts,
            env={"SCRIPT_MARKER": str(marker)},
            dry_run=False,
        )

    assert marker.read_text().splitlines() == [script.name for script in scripts] * 2


def test_script_preview_does_not_prepare_execute_or_repair_scripts(tmp_path, monkeypatch):
    scripts = [tmp_path / name for name in ("setup.py", "init_preview.sh", "setup.ps1")]
    for script in scripts:
        script.write_text("must not execute\n")
        script.chmod(0o600)
    modes = [script.stat().st_mode for script in scripts]
    monkeypatch.setattr(
        shell, "process_env", lambda *a: pytest.fail("preview prepared environment")
    )
    monkeypatch.setattr(
        shell.shutil, "which", lambda *a, **kw: pytest.fail("preview resolved an interpreter")
    )
    monkeypatch.setattr(
        shell.subprocess, "run", lambda *a, **kw: pytest.fail("preview executed a script")
    )

    machine_scripts.run_scripts(scripts, env={}, dry_run=True)

    assert [script.stat().st_mode for script in scripts] == modes


@pytest.mark.skipif(sys.platform == "win32", reason="Unix executable permissions")
def test_script_execution_does_not_repair_permissions(tmp_path):
    script = tmp_path / "not-executable.sh"
    script.write_text("#!/bin/sh\nexit 0\n")
    script.chmod(0o600)
    with pytest.raises(PermissionError):
        machine_scripts.run_scripts([script], env={}, dry_run=False)
    assert script.stat().st_mode & 0o777 == 0o600


@pytest.mark.skipif(sys.platform == "win32", reason="Unix script execution")
def test_unix_scripts_use_declared_shebang_and_environment(tmp_path, monkeypatch):
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
    script.write_text(
        '#!/bin/sh -e\nprintf "%s\\n" "$MC_ID|$MC_VALUE|$PATH" > "$RESULT"\nfalse\nexit 0\n'
    )
    script.chmod(0o755)
    with pytest.raises(subprocess.CalledProcessError) as failure:
        machine_scripts.run_scripts(
            [script], env={**environment, "RESULT": str(result)}, dry_run=False
        )
    assert failure.value.returncode == 1
    assert result.read_text().strip() == f"selected|private|{selected_path}"


@pytest.mark.parametrize("exit_code", [0, 7])
def test_docker_elevation_failure_stops_before_user_package_setup(tmp_path, exit_code):
    powershell = shutil.which("pwsh") or shutil.which("powershell.exe")
    if powershell is None:
        pytest.skip("PowerShell is unavailable")
    script = Path(__file__).parents[1] / "machines/pc/scripts/init_docker.win.ps1"
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
    powershell = shutil.which("pwsh") or shutil.which("powershell.exe")
    if powershell is None:
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
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(harness),
            str(script),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("outcome", ["success", "failure", "restart"])
def test_ssh_skips_installed_capabilities_and_stops_on_install_failure(tmp_path, outcome):
    powershell = shutil.which("pwsh") or shutil.which("powershell.exe")
    if powershell is None:
        pytest.skip("PowerShell is unavailable")
    script = machine_env.ROOT / "config/ssh/scripts/init_ssh.win.ps1"
    harness = tmp_path / "ssh.ps1"
    harness.write_text(
        r"""
param($ScriptPath, $Outcome)
function Get-WindowsCapability {
    param([switch]$Online, $Name)
    $state = if ($Name -like 'OpenSSH.Client*') { 'Installed' } else { 'NotPresent' }
    [pscustomobject]@{ State = $state }
}
function Add-WindowsCapability {
    param([switch]$Online, $Name)
    if ($Name -notlike 'OpenSSH.Server*') { throw 'unexpected installation' }
    Write-Host 'install-server'
    if ($Outcome -eq 'failure') { throw 'installation failed' }
    [pscustomobject]@{ RestartNeeded = $Outcome -eq 'restart' }
}
function Get-Service { 'sshd' }
function Set-Service { }
function Start-Service { 'service-started' }
& $ScriptPath -Admin
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
            outcome,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.stdout.count("install-server") == 1, result.stdout + result.stderr
    assert (result.returncode == 0) == (outcome == "success"), result.stdout + result.stderr
    assert ("service-started" in result.stdout) == (outcome == "success")
