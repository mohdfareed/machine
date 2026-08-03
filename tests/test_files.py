"""File deployment tests."""

import os
import re
import stat
import subprocess
from pathlib import Path

import pytest

from machine.ops import files as machine_files


class _WindowsPrivilegeError(OSError):
    """Typed Windows symlink privilege error used by tests."""

    winerror: int

    def __init__(self) -> None:
        super().__init__("symlink requires privilege")
        self.winerror = 1314


def test_symlink_raises_guidance_on_windows_file_privilege_error(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Windows file links should explain how to enable symlink privileges."""
    source = tmp_path / "source.txt"
    target = tmp_path / "target.txt"
    source.write_text("git config", encoding="utf-8")

    def _deny_symlink(self: Path, link_target: Path, target_is_directory: bool = False) -> None:
        raise _WindowsPrivilegeError()

    monkeypatch.setattr(machine_files, "is_windows", True)
    monkeypatch.setattr(machine_files.settings, "dry_run", False)
    monkeypatch.setattr(Path, "symlink_to", _deny_symlink)

    with pytest.raises(
        OSError,
        match=re.escape("Symlink creation failed - enable Developer Mode first."),
    ):
        machine_files._symlink(source, target)

    assert not target.exists()


def test_symlink_raises_guidance_on_windows_directory_privilege_error(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Windows directory links should explain how to enable symlink privileges."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    (source / "config.txt").write_text("ssh", encoding="utf-8")

    def _deny_symlink(self: Path, link_target: Path, target_is_directory: bool = False) -> None:
        raise _WindowsPrivilegeError()

    monkeypatch.setattr(machine_files, "is_windows", True)
    monkeypatch.setattr(machine_files.settings, "dry_run", False)
    monkeypatch.setattr(Path, "symlink_to", _deny_symlink)

    with pytest.raises(
        OSError,
        match=re.escape("Symlink creation failed - enable Developer Mode first."),
    ):
        machine_files._symlink(source, target)

    assert not target.exists()


def test_symlink_skips_existing_hardlink(tmp_path: Path) -> None:
    """Re-applying an already-correct hard link should be a no-op."""
    source = tmp_path / "source.txt"
    target = tmp_path / "target.txt"
    source.write_text("ssh config", encoding="utf-8")
    os.link(source, target)

    changed = machine_files._symlink(source, target)

    assert changed is False
    assert not (tmp_path / "target.txt.backup").exists()


@pytest.mark.skipif(os.name == "nt", reason="Windows uses ACLs instead of POSIX modes")
def test_symlink_applies_mode_to_existing_link(
    monkeypatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.txt"
    target = tmp_path / "target.txt"
    source.write_text("ssh config", encoding="utf-8")
    target.symlink_to(source)
    source.chmod(0o644)

    monkeypatch.setattr(machine_files, "is_windows", False)

    changed = machine_files._symlink(source, target, 0o600)

    assert changed is True
    assert stat.S_IMODE(source.stat().st_mode) == 0o600


def test_symlink_applies_private_windows_acl_to_source_and_link(
    monkeypatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.txt"
    target = tmp_path / "target.txt"
    source.write_text("ssh config", encoding="utf-8")
    target.symlink_to(source)
    commands: list[list[object]] = []

    def _run(command: list[object], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return subprocess.CompletedProcess("command", 0, stdout="user", stderr="")

    monkeypatch.setattr(machine_files, "is_windows", True)
    monkeypatch.setattr(machine_files.subprocess, "run", _run)

    machine_files._symlink(source, target, 0o600)

    assert any(command[0] == "icacls" and command[1] == source for command in commands)
    assert any(
        command[0] == "icacls" and command[1] == target and "/L" in command for command in commands
    )


def test_symlink_uses_next_backup_name_when_backup_exists(tmp_path: Path) -> None:
    """Replacing an existing file should not fail if .backup already exists."""
    source = tmp_path / "source.json"
    target = tmp_path / "settings.json"
    source.write_text('{"editor.tabSize": 4}', encoding="utf-8")
    target.write_text('{"editor.tabSize": 2}', encoding="utf-8")
    (tmp_path / "settings.json.backup").write_text("older backup", encoding="utf-8")

    changed = machine_files._symlink(source, target)

    assert changed is True
    assert (tmp_path / "settings.json.backup").read_text(encoding="utf-8") == "older backup"
    assert (tmp_path / "settings.json.backup.1").read_text(
        encoding="utf-8"
    ) == '{"editor.tabSize": 2}'
    assert os.path.samefile(source, target)
