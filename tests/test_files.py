"""File preservation, preview decisions, and platform permissions."""

import os
import stat
import subprocess
from pathlib import Path

import pytest
from app.configuration.models import FileMapping
from app.deployment import files as machine_files


@pytest.mark.parametrize("dry_run", [False, True])
def test_missing_source_fails_before_target_changes(tmp_path, dry_run):
    target = tmp_path / "target"
    target.write_text("existing")
    mapping = FileMapping(source=str(tmp_path / "missing"), target=target)
    with pytest.raises(FileNotFoundError):
        machine_files.deploy_file(mapping, env={}, dry_run=dry_run)
    assert target.read_text() == "existing"
    assert not (tmp_path / "target.backup").exists()


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

    def deny_link(self, link_source, *, target_is_directory):
        assert self == target and link_source == source
        assert target_is_directory is is_directory
        raise PermissionError("link denied")

    monkeypatch.setattr(Path, "symlink_to", deny_link)
    with pytest.raises(OSError) as error:
        machine_files.deploy_file(FileMapping(source=source, target=target), env={}, dry_run=False)
    assert str(backup) in str(error.value)
    assert backup_data.read_text() == "existing"
    assert source_data.read_text() == "new"
    assert not target.exists()


def test_failed_backup_leaves_target_intact(monkeypatch, tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.write_text("new")
    target.write_text("existing")
    failure = PermissionError("backup denied")

    def deny_rename(self, destination):
        raise failure

    monkeypatch.setattr(Path, "rename", deny_rename)
    with pytest.raises(PermissionError) as caught:
        machine_files.deploy_file(FileMapping(source=source, target=target), env={}, dry_run=False)
    assert caught.value is failure
    assert target.read_text() == "existing"
    assert not (tmp_path / "target.backup").exists()


def test_preview_does_not_create_target_directory(tmp_path):
    source = tmp_path / "source"
    source.write_text("settings")
    target = tmp_path / "missing" / "target"
    machine_files.deploy_file(
        FileMapping(source=source, target=target, mode=0o600), env={}, dry_run=True
    )
    assert not target.parent.exists()


def test_existing_hard_link_is_unchanged(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.write_text("settings")
    os.link(source, target)
    machine_files.deploy_file(FileMapping(source=source, target=target), env={}, dry_run=False)
    assert target.samefile(source)
    assert not target.is_symlink()
    assert not (tmp_path / "target.backup").exists()


def test_correct_relative_symlink_is_unchanged(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.write_text("settings")
    target.symlink_to(source.name)
    mapping = FileMapping(source=source, target=target)
    machine_files.deploy_file(mapping, env={}, dry_run=True)
    machine_files.deploy_file(mapping, env={}, dry_run=False)
    assert target.readlink() == Path(source.name)
    assert not (tmp_path / "target.backup").exists()


@pytest.mark.parametrize("dangling", [False, True], ids=["existing", "dangling"])
def test_replaces_other_symlink_without_changing_its_source(tmp_path, dangling):
    source = tmp_path / "source"
    previous_source = tmp_path / "previous"
    target = tmp_path / "target"
    source.write_text("new")
    if not dangling:
        previous_source.write_text("existing")
    target.symlink_to(previous_source)
    mapping = FileMapping(source=source, target=target)

    machine_files.deploy_file(mapping, env={}, dry_run=True)
    assert target.readlink() == previous_source
    machine_files.deploy_file(mapping, env={}, dry_run=False)
    assert target.readlink() == source
    assert target.read_text() == "new"
    assert not (tmp_path / "target.backup").exists()
    if not dangling:
        assert previous_source.read_text() == "existing"
    assert previous_source.exists() is not dangling


@pytest.mark.skipif(os.name == "nt", reason="Windows uses ACLs instead of POSIX modes")
def test_permissions_apply_to_correct_link_without_preview_mutation(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.write_text("settings")
    source.chmod(0o644)
    target.symlink_to(source)
    mapping = FileMapping(source=source, target=target, mode=0o600)
    machine_files.deploy_file(mapping, env={}, dry_run=True)
    assert stat.S_IMODE(source.stat().st_mode) == 0o644
    for _ in range(2):
        machine_files.deploy_file(mapping, env={}, dry_run=False)
        assert stat.S_IMODE(source.stat().st_mode) == 0o600
        assert target.readlink() == source
    assert not (tmp_path / "target.backup").exists()


def test_windows_acl_reset_clears_explicit_grants_and_preview_does_not_write(monkeypatch, tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.write_text("settings")
    target.symlink_to(source)
    mapping = FileMapping(source=source, target=target, mode=0o600)
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
    machine_files.deploy_file(mapping, env=env, dry_run=True)
    assert commands == []
    assert source.stat().st_mode == original_mode
    machine_files.deploy_file(mapping, env=env, dry_run=False)
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
    commands.clear()
    machine_files.deploy_file(mapping, env=env, dry_run=True)
    assert commands == []
    assert target.readlink() == source


@pytest.mark.parametrize("dangling_backup", [False, True])
def test_numbered_backups_are_preserved(tmp_path, dangling_backup):
    source = tmp_path / "source.json"
    target = tmp_path / "settings.json"
    source.write_text("new")
    target.write_text("existing")
    backup = tmp_path / "settings.json.backup"
    if dangling_backup:
        backup.symlink_to(tmp_path / "missing")
    else:
        backup.write_text("older")
    mapping = FileMapping(source=source, target=target)
    machine_files.deploy_file(mapping, env={}, dry_run=True)
    assert target.read_text() == "existing"
    assert not (tmp_path / "settings.json.backup.1").exists()
    machine_files.deploy_file(mapping, env={}, dry_run=False)
    if dangling_backup:
        assert backup.is_symlink() and backup.readlink() == tmp_path / "missing"
    else:
        assert backup.read_text() == "older"
    assert (tmp_path / "settings.json.backup.1").read_text() == "existing"
    assert os.path.samefile(source, target)


@pytest.mark.parametrize("existing_target", ["link", "file", "missing"])
def test_windows_acl_failure_preserves_link_and_backup(monkeypatch, tmp_path, existing_target):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.write_text("settings")
    if existing_target == "link":
        target.symlink_to(source)
    if existing_target == "file":
        target.write_text("existing")
    monkeypatch.setattr(machine_files, "is_windows", True)
    monkeypatch.setattr(
        machine_files,
        "query",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, stdout="user\n"),
    )

    failure = subprocess.CalledProcessError(1, ["icacls", str(target)])

    def run(command, **kwargs):
        if "/L" in command:
            raise failure

    monkeypatch.setattr(machine_files, "run", run)
    monkeypatch.setattr(Path, "unlink", lambda *args: pytest.fail("removed link after ACL failure"))
    error_type = OSError if existing_target == "file" else subprocess.CalledProcessError
    with pytest.raises(error_type) as caught:
        machine_files.deploy_file(
            FileMapping(source=source, target=target, mode=0o600), env={}, dry_run=False
        )
    if existing_target == "file":
        backup = tmp_path / "target.backup"
        assert caught.value.__cause__ is failure
        assert str(backup) in str(caught.value)
        assert backup.read_text() == "existing"
    else:
        assert caught.value is failure
        assert not (tmp_path / "target.backup").exists()
    assert target.readlink() == source
    assert source.read_text() == "settings"
