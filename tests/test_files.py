"""File preservation, preview decisions, and platform permissions."""

import os
import stat
import subprocess
from pathlib import Path

import pytest

from app.models import FileMapping
from app.ops import files as machine_files


def test_missing_source_fails_before_target_changes(tmp_path):
    target = tmp_path / "target"
    target.write_text("existing")
    mapping = FileMapping(source=str(tmp_path / "missing"), target=str(target))
    with pytest.raises(FileNotFoundError):
        machine_files.deploy_file(mapping, env={}, dry_run=False)
    assert target.read_text() == "existing"


@pytest.mark.parametrize("is_directory", [False, True], ids=["file", "directory"])
def test_failed_link_preserves_data_and_reports_backup(monkeypatch, tmp_path, is_directory):
    source = tmp_path / "source"
    target = tmp_path / "target"
    backup = tmp_path / "target.backup"
    if is_directory:
        source.mkdir()
        target.mkdir()
    source_data = source / "data" if is_directory else source
    target_data = target / "data" if is_directory else target
    backup_data = backup / "data" if is_directory else backup
    source_data.write_text("new")
    target_data.write_text("existing")

    def deny_link(*args, **kwargs):
        raise PermissionError("link denied")

    monkeypatch.setattr(machine_files, "_create_link", deny_link)
    with pytest.raises(OSError) as error:
        machine_files.deploy_file(
            FileMapping(source=str(source), target=str(target)), env={}, dry_run=False
        )
    assert str(backup) in str(error.value)
    assert backup_data.read_text() == "existing"
    assert source_data.read_text() == "new"
    assert not target.exists()


def test_existing_hard_link_is_unchanged(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.write_text("settings")
    os.link(source, target)
    assert (
        machine_files.deploy_file(
            FileMapping(source=str(source), target=str(target)), env={}, dry_run=False
        )
        is None
    )
    assert not (tmp_path / "target.backup").exists()


@pytest.mark.skipif(os.name == "nt", reason="Windows uses ACLs instead of POSIX modes")
def test_permission_preview_matches_real_change(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.write_text("settings")
    source.chmod(0o644)
    target.symlink_to(source)
    mapping = FileMapping(source=str(source), target=str(target), mode=0o600)
    assert machine_files.deploy_file(mapping, env={}, dry_run=True) == target
    assert stat.S_IMODE(source.stat().st_mode) == 0o644
    assert machine_files.deploy_file(mapping, env={}, dry_run=False) == target
    assert stat.S_IMODE(source.stat().st_mode) == 0o600
    assert machine_files.deploy_file(mapping, env={}, dry_run=True) is None


def test_windows_acl_reset_clears_explicit_grants_and_preview_does_not_write(monkeypatch, tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.write_text("settings")
    target.symlink_to(source)
    mapping = FileMapping(source=str(source), target=str(target), mode=0o600)
    env = {"PATH": "chosen-path"}
    commands = []
    monkeypatch.setattr(machine_files, "is_windows", True)
    monkeypatch.setattr(
        machine_files,
        "query",
        lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, 0, stdout="domain\\user\n"),
    )

    def run(command, **kwargs):
        assert kwargs["env"] is env
        assert kwargs["dry_run"] is False
        commands.append(command)

    monkeypatch.setattr(machine_files, "run", run)
    original_mode = source.stat().st_mode
    assert machine_files.deploy_file(mapping, env=env, dry_run=True) == target
    assert commands == []
    assert source.stat().st_mode == original_mode
    assert machine_files.deploy_file(mapping, env=env, dry_run=False) == target
    for path, suffix in ((source, []), (target, ["/L"])):
        assert [command for command in commands if command[1] == str(path)] == [
            ["icacls", str(path), "/setowner", "domain\\user", *suffix],
            ["icacls", str(path), "/reset", *suffix],
            [
                "icacls",
                str(path),
                "/inheritance:r",
                "/grant:r",
                "domain\\user:(F)",
                "*S-1-5-18:(F)",
                *suffix,
            ],
        ]
    assert machine_files.deploy_file(mapping, env=env, dry_run=True) == target


def test_numbered_backups_are_preserved(tmp_path):
    source = tmp_path / "source.json"
    target = tmp_path / "settings.json"
    source.write_text("new")
    target.write_text("existing")
    (tmp_path / "settings.json.backup").write_text("older")
    mapping = FileMapping(source=str(source), target=str(target))
    assert machine_files.deploy_file(mapping, env={}, dry_run=True) == target
    assert target.read_text() == "existing"
    assert machine_files.deploy_file(mapping, env={}, dry_run=False) == target
    assert (tmp_path / "settings.json.backup").read_text() == "older"
    assert (tmp_path / "settings.json.backup.1").read_text() == "existing"
    assert os.path.samefile(source, target)
