"""Selected environment construction and saved-default behavior."""

import shutil
import subprocess
import sys
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest
from app import env


def test_build_env_uses_literal_declarations_without_saving_or_inheriting(tmp_path, monkeypatch):
    directory = tmp_path / "mc"
    monkeypatch.setattr(env, "config_dir", lambda: directory)
    monkeypatch.setenv("MC_ID", "inherited")
    monkeypatch.setenv("CALLER_SECRET", "not-declared")
    values = {"DEV": tmp_path / "Dev", "LITERAL": "$DEV/bin", "MC_ID": "wrong"}

    result = env.build_env("test", values)

    assert result == {"DEV": str(tmp_path / "Dev"), "LITERAL": "$DEV/bin", "MC_ID": "test"}
    assert values["MC_ID"] == "wrong"
    assert not directory.exists()


def test_build_env_keeps_explicit_path_and_windows_base_precedence(monkeypatch):
    monkeypatch.setattr(env, "is_windows", True)
    monkeypatch.setenv("PATH", "inherited")

    assert env.build_env("test", {"Path": "configured", "mc_id": "wrong"}) == {
        "PATH": "configured",
        "MC_ID": "test",
    }


@pytest.mark.parametrize("shell", ["fish", "pwsh"])
def test_saved_shell_environment_round_trips_literal_values(tmp_path, monkeypatch, shell):
    executable = shutil.which(shell)
    if executable is None:
        pytest.skip(f"{shell} is not installed")
    directory = tmp_path / "mc"
    monkeypatch.setattr(env, "config_dir", lambda: directory)
    monkeypatch.setattr(env, "is_windows", False)
    monkeypatch.setenv("CALLER_SECRET", "not-declared")
    value = (
        "quotes: '\u2018\u2019\u201a\u201b \"; dollar: $HOME $(echo injected); slash: \\\n"
        "second line\r\n"
    )
    values = env.build_env("test", {"PUBLIC": value})
    env.save_machine("test", values)

    if shell == "fish":
        script = tmp_path / "read.fish"
        script.write_text("source $argv[1]\nprintf '%s' \"$PUBLIC\"\n")
        arguments = [executable, "--no-config", str(script), str(directory / "env.fish")]
    else:
        script = tmp_path / "read.ps1"
        script.write_text(
            "param($EnvironmentFile)\n. $EnvironmentFile\n[Console]::Write($env:PUBLIC)"
        )
        arguments = [executable, "-NoProfile", "-File", str(script), str(directory / "env.ps1")]

    result = subprocess.run(arguments, capture_output=True, check=True)
    assert result.stdout.decode("utf-8") == value
    assert env.get_current_machine() == "test"
    for path in directory.iterdir():
        assert "CALLER_SECRET" not in path.read_text()


@pytest.mark.parametrize(
    ("overrides", "tool_home", "expected_paths"),
    [
        (
            {},
            r"C:\New Tool",
            [r"C:\Windows\System32", r"C:\New Tool\bin", r"C:\New Tool\SDK\bin"],
        ),
        (
            {"tool_home": r"D:\Selected Tool"},
            r"D:\Selected Tool",
            [r"C:\Windows\System32", r"D:\Selected Tool\bin", r"D:\Selected Tool\SDK\bin"],
        ),
        ({"pAtH": r"D:\Selected\bin"}, r"C:\New Tool", [r"D:\Selected\bin"]),
    ],
)
def test_system_env_expands_fresh_windows_values_and_preserves_caller_paths(
    monkeypatch, overrides, tool_home, expected_paths
):
    machine_values = [
        ("SystemRoot", r"C:\Windows", 1),
        ("Tool_Home", r"C:\New Tool", 1),
        ("Path", r"%SystemRoot%\System32;%tool_home%\bin", 2),
    ]
    user_values = [
        ("SDK_ROOT", r"%Tool_Home%\SDK", 2),
        ("Path", r"%sdk_root%\bin", 2),
    ]
    registry = SimpleNamespace(
        HKEY_LOCAL_MACHINE="machine",
        HKEY_CURRENT_USER="user",
        REG_EXPAND_SZ=2,
        OpenKey=lambda hive, key: nullcontext(machine_values if hive == "machine" else user_values),
        QueryInfoKey=lambda values: (0, len(values), 0),
        EnumValue=lambda values, index: values[index],
    )
    inherited = {
        "Path": r"C:\Temporary\bin;c:\windows\system32;C:\Old Tool\bin",
        "TOOL_HOME": r"C:\Old Tool",
        "CALLER_ONLY": "retained",
    }
    monkeypatch.setitem(sys.modules, "winreg", registry)
    monkeypatch.setattr(env.os, "environ", inherited)
    monkeypatch.setattr(env.sys, "platform", "win32")

    result = env.system_env(overrides)

    assert result["TOOL_HOME"] == tool_home
    assert result["SDK_ROOT"] == tool_home + r"\SDK"
    assert result["CALLER_ONLY"] == "retained"
    if "pAtH" not in overrides:
        expected_paths = [*expected_paths, r"C:\Temporary\bin", r"C:\Old Tool\bin"]
    assert result["PATH"].split(";") == expected_paths
    assert inherited["TOOL_HOME"] == r"C:\Old Tool"


def test_system_env_on_unix_applies_overrides_without_changing_caller_state(monkeypatch):
    monkeypatch.setattr(env.sys, "platform", "linux")
    monkeypatch.setattr(env.os, "environ", {"PATH": "/caller/bin", "CALLER_ONLY": "retained"})

    result = env.system_env({"PATH": "/selected/bin"})

    assert result == {"PATH": "/selected/bin", "CALLER_ONLY": "retained"}
    assert env.os.environ["PATH"] == "/caller/bin"


def test_machine_selection_reads_saved_file_instead_of_shell(tmp_path, monkeypatch):
    directory = tmp_path / "mc"
    monkeypatch.setattr(env, "config_dir", lambda: directory)
    monkeypatch.setattr(env, "is_windows", True)
    monkeypatch.setenv("MC_ID", "stale")

    assert env.get_current_machine() is None
    env.save_machine("next", env.build_env("next", {}))
    assert env.get_current_machine() == "next"
    assert (directory / "machine").read_text() == "next\n"
    assert (directory / "env.ps1").is_file()
    assert not (directory / "env.fish").exists()
    (directory / "machine").write_text("")
    assert env.get_current_machine() is None


def test_paths_use_supplied_environment_and_reject_unresolved_targets(tmp_path, monkeypatch):
    values = {"DEV": str(tmp_path), "HOME": str(tmp_path), "USERPROFILE": str(tmp_path)}
    assert env.resolve_path(Path("$DEV/config"), values) == tmp_path / "config"
    assert env.resolve_path(Path("~/.config"), values) == tmp_path / ".config"
    with pytest.raises(ValueError, match="Unresolved path variable"):
        env.resolve_path(Path("$MISSING/config"), values)
    with pytest.raises(ValueError, match="must be absolute"):
        env.resolve_path(Path("relative/config"), values)
    monkeypatch.setattr(env, "is_windows", True)
    assert env.resolve_path(Path("%Dev%/config"), values) == tmp_path / "config"
    values["DEV"] = str(tmp_path / "$literal")
    assert env.resolve_path(Path("$DEV/config"), values) == tmp_path / "$literal" / "config"
