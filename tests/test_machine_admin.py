"""Admin failures print once and stop the script without a second error record."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(sys.platform != "win32", reason="Windows elevation helper")
@pytest.mark.parametrize("already_admin", [False, True])
@pytest.mark.parametrize("mode,exit_code", [("success", 0), ("throw", 1), ("native", 7)])
def test_admin_output_and_failure_status(tmp_path: Path, already_admin, mode, exit_code):
    shell = shutil.which("powershell.exe")
    if shell is None:
        pytest.skip("Windows PowerShell is unavailable")
    source = Path(__file__).parents[1] / "src/machine/powershell/MachineAdmin/MachineAdmin.psm1"
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
