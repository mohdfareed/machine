"""Selected environment construction and saved-default behavior."""

import sys
from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from app import env


def test_build_env_resolves_private_path_without_saving_selection(tmp_path, monkeypatch):
    root = tmp_path / "root"
    private = tmp_path / "private"
    machine_dir = root / "machines" / "test"
    machine_dir.mkdir(parents=True)
    (private / "env").mkdir(parents=True)
    env_file = tmp_path / ".env"
    env_file.write_text("MC_ID=previous\n")
    monkeypatch.setattr(env, "_ENV_FILE", env_file)
    monkeypatch.setattr(env, "ROOT", root)
    monkeypatch.setenv("MC_ID", "inherited")
    monkeypatch.setenv("PRIVATE_SOURCE", str(private))
    monkeypatch.setenv("CALLER_ONLY", "inherited")
    monkeypatch.delenv("TAILNET_NAME", raising=False)
    (machine_dir / "machine.env").write_text(
        'PRIVATE_ROOT="$PRIVATE_SOURCE"\nMC_PRIVATE="$PRIVATE_ROOT"\n'
    )
    (private / "env" / "test.env").write_text(
        'TAILNET_NAME="example"\nMC_ID=wrong\nMC_PRIVATE=/wrong\n'
    )

    result = env.build_env("test")

    assert result["MC_PRIVATE"] == str(private)
    assert result["MC_ID"] == "test"
    assert result["TAILNET_NAME"] == "example"
    assert "PRIVATE_SOURCE" not in result
    assert "CALLER_ONLY" not in result
    assert "PATH" not in result
    assert env_file.read_text() == "MC_ID=previous\n"
    assert "TAILNET_NAME" not in env.build_env("test", include_private=False)


def test_build_env_keeps_explicit_path_and_windows_base_precedence(tmp_path, monkeypatch):
    machine_dir = tmp_path / "machines" / "test"
    machine_dir.mkdir(parents=True)
    monkeypatch.setattr(env, "ROOT", tmp_path)
    monkeypatch.setattr(env, "is_windows", True)
    monkeypatch.setenv("PATH", "inherited")
    (machine_dir / "machine.env").write_text(
        """Path="configured"
mc_id=wrong
"""
    )

    result = env.build_env("test", include_private=False)

    assert result["PATH"] == "configured"
    assert result["MC_ID"] == "test"


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


def test_machine_selection_reads_env_file_instead_of_shell(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    monkeypatch.setattr(env, "_ENV_FILE", env_file)
    monkeypatch.setattr(env, "ROOT", tmp_path)
    monkeypatch.setenv("MC_ID", "stale")

    assert env.get_current_machine() is None
    env_file.write_text('# Machine selection\nMC_ID="current"\n')
    assert env.get_current_machine() == "current"
    assert env.build_env("current")["MC_MACHINE"] == str(tmp_path / "machines" / "current")

    env.set_current_machine("next")
    assert env.get_current_machine() == "next"
    env_file.write_text("MC_ID=\n")
    assert env.get_current_machine() is None


def test_paths_use_supplied_environment_and_reject_unresolved_targets(tmp_path, monkeypatch):
    values = {"DEV": str(tmp_path), "HOME": str(tmp_path), "USERPROFILE": str(tmp_path)}
    assert env.resolve_path("$DEV/config", values) == tmp_path / "config"
    assert env.resolve_path("~/.config", values) == tmp_path / ".config"
    with pytest.raises(ValueError, match="Unresolved path variable"):
        env.resolve_path("$MISSING/config", values)
    with pytest.raises(ValueError, match="must be absolute"):
        env.resolve_path("relative/config", values)
    monkeypatch.setattr(env, "is_windows", True)
    assert env.resolve_path("%Dev%/config", values) == tmp_path / "config"
