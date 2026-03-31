"""File deployment tests."""

import os
import subprocess
from pathlib import Path

from machine.ops import files as machine_files


def test_symlink_falls_back_to_hardlink_on_windows_privilege_error(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Windows file links should fall back to hard links without admin rights."""
    source = tmp_path / "source.txt"
    target = tmp_path / "target.txt"
    source.write_text("git config", encoding="utf-8")

    def _deny_symlink(self: Path, link_target: Path, target_is_directory: bool = False) -> None:
        err = OSError("symlink requires privilege")
        err.winerror = 1314
        raise err

    monkeypatch.setattr(machine_files, "is_windows", True)
    monkeypatch.setattr(machine_files.settings, "dry_run", False)
    monkeypatch.setattr(Path, "symlink_to", _deny_symlink)

    changed = machine_files._symlink(source, target)

    assert changed is True
    assert target.exists()
    assert os.path.samefile(source, target)


def test_symlink_falls_back_to_junction_on_windows_privilege_error(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Windows directory links should fall back to junctions without admin rights."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    (source / "config.txt").write_text("ssh", encoding="utf-8")

    def _deny_symlink(self: Path, link_target: Path, target_is_directory: bool = False) -> None:
        err = OSError("symlink requires privilege")
        err.winerror = 1314
        raise err

    def _fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        assert cmd == ["cmd", "/c", "mklink", "/J", str(target), str(source)]
        target.mkdir()
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(machine_files, "is_windows", True)
    monkeypatch.setattr(machine_files.settings, "dry_run", False)
    monkeypatch.setattr(Path, "symlink_to", _deny_symlink)
    monkeypatch.setattr(machine_files.subprocess, "run", _fake_run)

    changed = machine_files._symlink(source, target)

    assert changed is True
    assert target.exists()
    assert target.is_dir()


def test_symlink_skips_existing_hardlink(tmp_path: Path) -> None:
    """Re-applying an already-correct hard link should be a no-op."""
    source = tmp_path / "source.txt"
    target = tmp_path / "target.txt"
    source.write_text("ssh config", encoding="utf-8")
    os.link(source, target)

    changed = machine_files._symlink(source, target)

    assert changed is False
    assert not (tmp_path / "target.txt.backup").exists()


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
    assert (tmp_path / "settings.json.backup.1").read_text(encoding="utf-8") == '{"editor.tabSize": 2}'
    assert os.path.samefile(source, target)
