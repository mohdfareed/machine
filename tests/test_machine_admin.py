"""Exercise the admin output relay without requesting elevation or changing the machine."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(sys.platform != "win32", reason="Windows elevation helper")
def test_admin_relay_streams_output_and_preserves_failures(tmp_path: Path):
    shell = shutil.which("powershell.exe")
    if shell is None:
        pytest.skip("Windows PowerShell is unavailable")
    module = Path(__file__).parents[1] / "src/machine/powershell/MachineAdmin/MachineAdmin.psm1"
    # Force the relay branch even if the test runner itself is elevated.
    copy = tmp_path / "MachineAdmin.psm1"
    copy.write_text(
        module.read_text().replace(
            "if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))",
            "if ($false)",
        ),
        encoding="utf-8",
    )
    script = tmp_path / "relay.ps1"
    script.write_text(
        "$ErrorActionPreference = 'Stop'\n"
        f"$module = Import-Module '{str(copy).replace(chr(39), chr(39) * 2)}' -PassThru\n"
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
    param($message)
    Write-Host $message
    Start-Sleep -Seconds 1
    Write-Output 'relay-output'
    Write-Warning 'relay-warning'
    Write-Verbose 'relay-verbose' -Verbose
} -ArgumentList "relay-host 'quoted'"
try {
    Invoke-Admin { Write-Host 'before-throw'; throw 'relay-error' }
    throw 'expected failure'
}
catch {
    if ($_.Exception.Message -ne 'Admin block failed (exit 1).') { throw }
    Write-Host 'caught-throw'
}
try {
    Invoke-Admin { cmd.exe /c 'echo native-output & exit 7' }
    throw 'expected native failure'
}
catch {
    if ($_.Exception.Message -ne 'Admin block failed (exit 7).') { throw }
    Write-Host 'caught-native'
}
& $module { function script:Start-Process { throw 'simulated cancellation' } }
try {
    Invoke-Admin { 'must not run' }
    throw 'expected cancellation'
}
catch {
    if ($_.Exception.Message -notlike 'Could not obtain administrator access:*') { throw }
    Write-Host 'caught-cancellation'
}
""",
        encoding="utf-8",
    )
    process = subprocess.Popen(
        [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert process.stdout is not None
    output = ""
    try:
        for line in process.stdout:
            output += line
            if "relay-host 'quoted'" in line:
                assert process.poll() is None, "output was buffered until the relay completed"
        assert process.wait(timeout=30) == 0, output
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
    for message in (
        "relay-host 'quoted'",
        "relay-output",
        "relay-warning",
        "relay-verbose",
        "before-throw",
        "relay-error",
        "caught-throw",
        "native-output",
        "caught-native",
        "caught-cancellation",
    ):
        assert message in output, output
