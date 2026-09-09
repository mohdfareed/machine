"""Windows command transport must preserve PowerShell source and failures."""

import os
import sys

import pytest

from machine import core


@pytest.mark.skipif(sys.platform != "win32", reason="Windows PowerShell command transport")
@pytest.mark.parametrize(
    "command,expected,code",
    [
        (
            '$env:STEAM_INPUT_BRIDGE_REPO = "$env:DEV\\SteamInputBridge"; '
            "Write-Output $env:STEAM_INPUT_BRIDGE_REPO",
            r"C:\Dev Projects\SteamInputBridge",
            0,
        ),
        ('Write-Output "quoted value" | ForEach-Object { "[$_]" }', "[quoted value]", 0),
        (
            "Write-Host 'host output'; Write-Warning 'warning output'; "
            "Write-Progress -Activity 'probe' -Status 'probe'",
            "warning output",
            0,
        ),
        ('Write-Host "before error"; throw "example failure"', "example failure", 1),
        ('cmd.exe /c "echo native output & exit 7"', "native output", 1),
    ],
)
def test_windows_commands_preserve_source_and_failure(command, expected, code, capfd):
    rc, output = core._tee_pipe(command, {**os.environ, "DEV": r"C:\Dev Projects"})
    assert b"CLIXML" not in output
    assert rc == code
    assert expected in output.decode(errors="replace")
