"""File deployment tests."""

import os
import stat
import subprocess
from pathlib import Path

import pytest

from app.models import FileMapping, Platform
from app.ops import files as machine_files


class _WindowsPrivilegeError(OSError):
    """Typed Windows symlink privilege error used by tests."""

    winerror: int

    def __init__(self) -> None:
        super().__init__("symlink requires privilege")
        self.winerror = 1314


def test_deploy_files_skips_non_applicable_platforms(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    universal_source = tmp_path / "universal"
    windows_source = tmp_path / "windows"
    macos_source = tmp_path / "macos"
    for source in (universal_source, windows_source, macos_source):
        source.write_text(source.name, encoding="utf-8")

    mappings = [
        FileMapping(source=str(universal_source), target="universal-target"),
        FileMapping(
            source=str(windows_source),
            target="windows-target",
            platforms=[Platform.WINDOWS],
        ),
        FileMapping(
            source=str(macos_source),
            target="macos-target",
            platforms=[Platform.MACOS],
        ),
    ]
    linked: list[tuple[Path, Path]] = []

    def _record_link(source: Path, target: Path, _mode: int | None = None) -> bool:
        linked.append((source, target))
        return True

    monkeypatch.setattr(machine_files, "PLATFORM", Platform.WINDOWS)
    monkeypatch.setattr(machine_files, "_symlink", _record_link)

    result = machine_files.deploy_files(mappings)

    assert result.created == 2
    assert result.failures == []
    assert [source for source, _target in linked] == [universal_source, windows_source]
    assert [str(target) for _source, target in linked] == ["universal-target", "windows-target"]


@pytest.mark.parametrize("is_directory", [False, True], ids=["file", "directory"])
def test_symlink_preserves_data_on_windows_privilege_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    is_directory: bool,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    backup = tmp_path / "target.backup"
    if is_directory:
        source.mkdir()
        target.mkdir()
    source_data = source / "config.txt" if is_directory else source
    target_data = target / "config.txt" if is_directory else target
    backup_data = backup / "config.txt" if is_directory else backup
    source_data.write_text("new settings", encoding="utf-8")
    target_data.write_text("existing settings", encoding="utf-8")
    failure = _WindowsPrivilegeError()

    def _deny_symlink(self: Path, link_target: Path, target_is_directory: bool = False) -> None:
        assert self == target
        assert link_target == source
        assert target_is_directory == is_directory
        raise failure

    monkeypatch.setattr(machine_files, "is_windows", True)
    monkeypatch.setattr(machine_files.settings, "dry_run", False)
    monkeypatch.setattr(Path, "symlink_to", _deny_symlink)

    with pytest.raises(OSError) as error:
        machine_files._symlink(source, target)

    assert error.value.__cause__ is failure
    assert source_data.read_text(encoding="utf-8") == "new settings"
    assert backup_data.read_text(encoding="utf-8") == "existing settings"
    assert not target.exists()
    assert not target.is_symlink()


def test_symlink_skips_existing_hardlink(tmp_path: Path) -> None:
    """Redeploying an already-correct hard link should be a no-op."""
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
