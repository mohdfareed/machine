"""CLI lifecycle regression tests."""

import os
import subprocess
from pathlib import Path

import pytest
import typer
from app import cli, env, validation
from app.cli import deploy, entry, info, sync, upgrade
from typer.testing import CliRunner


@pytest.fixture(autouse=True)
def isolate_disk_access_probe(monkeypatch):
    monkeypatch.setattr(entry, "validate_full_disk_access", lambda: None)


@pytest.mark.parametrize("state", ["allowed", "missing", "denied"])
def test_full_disk_access_probe_does_not_read_contents(monkeypatch, state):
    from unittest.mock import mock_open

    monkeypatch.setattr(env, "is_macos", True)
    probe = mock_open()
    if state == "missing":
        probe.side_effect = FileNotFoundError
    if state == "denied":
        probe.side_effect = PermissionError
    monkeypatch.setattr(Path, "open", probe)

    if state == "denied":
        with pytest.raises(PermissionError, match="Full Disk Access"):
            validation.validate_full_disk_access()
    else:
        validation.validate_full_disk_access()

    probe.assert_called_once_with("rb")
    probe.return_value.read.assert_not_called()


def test_full_disk_access_probe_skips_other_platforms(monkeypatch):
    monkeypatch.setattr(env, "is_macos", False)
    monkeypatch.setattr(Path, "open", lambda *a, **kw: pytest.fail("opened macOS file"))
    validation.validate_full_disk_access()


def test_startup_denial_blocks_commands_but_not_help_or_version(monkeypatch):
    def denied():
        raise PermissionError("Access denied")

    monkeypatch.setattr(entry, "validate_full_disk_access", denied)
    monkeypatch.setattr(
        info, "get_current_machine", lambda: pytest.fail("command ran before probe")
    )
    runner = CliRunner()
    app = entry._create_app()
    result = runner.invoke(app, ["show", "id"])
    assert isinstance(result.exception, PermissionError)
    assert runner.invoke(app, ["--help"]).exit_code == 0
    assert runner.invoke(app, ["--version"]).exit_code == 0


def test_startup_denial_exits_without_traceback(monkeypatch):
    def denied():
        raise PermissionError("Access denied")

    monkeypatch.setattr(entry, "validate_full_disk_access", denied)
    monkeypatch.setattr("sys.argv", ["mc", "show", "id"])
    monkeypatch.setattr(
        entry.reporting, "exception", lambda *a: pytest.fail("unexpected traceback")
    )
    with pytest.raises(SystemExit) as failure:
        entry.main()
    assert failure.value.code == 1


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def sync_repos(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Exercise real Git history without user identities, hooks, or network access.
    for name in tuple(os.environ):
        if name.upper().startswith("GIT_"):
            monkeypatch.delenv(name)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for role in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{role}_NAME", "Sync Test")
        monkeypatch.setenv(f"GIT_{role}_EMAIL", "sync@example.com")
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    git(canonical, "init", "-b", "main")
    (canonical / "config.txt").write_text("original\n")
    git(canonical, "add", ".")
    git(canonical, "commit", "-m", "Initial config")
    checkout = tmp_path / "checkout"
    git(tmp_path, "clone", str(canonical), str(checkout))
    # A fork's origin may be unrelated or unavailable; sync must ignore it.
    git(checkout, "remote", "set-url", "origin", str(tmp_path / "unavailable-fork"))
    monkeypatch.setattr(env, "ROOT", checkout)
    monkeypatch.setattr(sync, "_CANONICAL_REPO_URL", str(canonical))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    def run(cmd, **kwargs):
        if kwargs["dry_run"]:
            return None
        if cmd[0] != "git":
            return subprocess.CompletedProcess(cmd, 0, stdout=b"")

        result = subprocess.run(cmd, capture_output=True)
        if kwargs.get("check") and result.returncode != 0:
            raise RuntimeError("Command failed")
        return result

    monkeypatch.setattr(sync, "run", run)
    return canonical, checkout


def test_machine_validation_is_case_insensitive(monkeypatch):
    monkeypatch.setattr(cli, "list_machines", lambda: ["homelab", "macbook"])

    assert cli.validate_machine("HOMELAB") == "homelab"
    with pytest.raises(typer.BadParameter):
        cli.validate_machine("unknown")


def test_module_completion_uses_qualified_names_and_groups(monkeypatch):
    monkeypatch.setattr(
        cli, "list_modules", lambda: ["home.editor", "work.editor", "work.terminal.shell"]
    )
    assert [name for name, _ in cli.complete_modules("work")] == [
        "work",
        "work.editor",
        "work.terminal",
        "work.terminal.shell",
    ]
    assert cli.complete_modules("editor") == []


@pytest.mark.parametrize("command", ["deploy", "show"])
def test_machine_selection_is_read_at_invocation(tmp_path, monkeypatch, command):
    env_file = tmp_path / "mc" / "machine"
    env_file.parent.mkdir()
    monkeypatch.setattr(env, "config_dir", lambda: env_file.parent)
    monkeypatch.setenv("MC_ID", "stale")
    monkeypatch.setattr(cli, "list_machines", lambda: ["first", "second"])
    monkeypatch.setattr(info, "list_machines", lambda: ["first", "second"])
    monkeypatch.setattr(deploy, "list_machines", lambda: ["first", "second"])
    monkeypatch.setattr(env, "ROOT", tmp_path)
    selected = []

    def load_machine(machine_id, module_names=None):
        selected.append(machine_id)
        raise RuntimeError("Stop before deployment")

    monkeypatch.setattr(deploy, "load_machine", load_machine)
    monkeypatch.setattr(info, "load_machine", load_machine)
    persisted = []
    monkeypatch.setattr(deploy, "save_machine", lambda machine, env: persisted.append(machine))
    app = entry._create_app()
    runner = CliRunner()

    # A new machine can be selected, then a changed file supplies the next default.
    result = runner.invoke(app, [command], input="FIRST\n")
    assert isinstance(result.exception, RuntimeError)
    env_file.write_text("second\n")
    result = runner.invoke(app, [command], input="\n")
    assert isinstance(result.exception, RuntimeError)
    assert selected == ["first", "second"]
    assert persisted == []


@pytest.mark.parametrize("windows", [False, True], ids=["unix", "windows"])
def test_sync_restores_local_edits(sync_repos, monkeypatch, windows):
    canonical, checkout = sync_repos
    monkeypatch.setattr(env, "is_windows", windows)

    # Change different parts of the same tracked file locally and upstream.
    original = "".join(f"setting {i}\n" for i in range(10))
    (canonical / "config.txt").write_text(original)
    git(canonical, "commit", "-am", "Expand config")
    git(checkout, "fetch", str(canonical), "main")
    git(checkout, "merge", "--ff-only", "FETCH_HEAD")
    (checkout / "config.txt").write_text(original.replace("setting 0", "local edit"))
    (canonical / "config.txt").write_text(original.replace("setting 9", "upstream edit"))
    git(canonical, "commit", "-am", "Update config")
    expected = original.replace("setting 0", "local edit").replace("setting 9", "upstream edit")

    sync.sync()

    assert git(checkout, "rev-parse", "HEAD") == git(canonical, "rev-parse", "HEAD")
    assert (checkout / "config.txt").read_text() == expected


def test_sync_autostash_conflict_preserves_edits(sync_repos):
    canonical, checkout = sync_repos
    (checkout / "config.txt").write_text("local edit\n")
    (canonical / "config.txt").write_text("upstream edit\n")
    git(canonical, "commit", "-am", "Update config")

    with pytest.raises(RuntimeError):
        sync.sync()

    assert git(checkout, "ls-files", "--unmerged")
    assert git(checkout, "show", "stash@{0}:config.txt") == "local edit"


def test_sync_divergence_preserves_commits(sync_repos):
    canonical, checkout = sync_repos
    (checkout / "config.txt").write_text("local commit\n")
    git(checkout, "commit", "-am", "Local change")
    before = git(checkout, "rev-parse", "HEAD")
    (canonical / "config.txt").write_text("upstream commit\n")
    git(canonical, "commit", "-am", "Upstream change")

    with pytest.raises(RuntimeError):
        sync.sync()

    assert git(checkout, "rev-parse", "HEAD") == before


def test_sync_fetch_failure_preserves_checkout(sync_repos, monkeypatch):
    canonical, checkout = sync_repos
    git(checkout, "fetch", str(canonical), "main")
    before = git(checkout, "rev-parse", "HEAD")
    monkeypatch.setattr(sync, "_CANONICAL_REPO_URL", str(canonical / "missing"))

    with pytest.raises(RuntimeError):
        sync.sync()

    assert git(checkout, "rev-parse", "HEAD") == before


@pytest.mark.parametrize("windows", [False, True], ids=["unix", "windows"])
def test_sync_dry_run_does_not_fetch(sync_repos, monkeypatch, windows):
    _, checkout = sync_repos
    monkeypatch.setattr(env, "is_windows", windows)
    result = CliRunner().invoke(entry._create_app(), ["sync", "--dry-run"])
    assert result.exit_code == 0, result.exception
    assert not (checkout / ".git" / "FETCH_HEAD").exists()
    assert not (checkout.parent / "config/fish/completions/mc.fish").exists()
    assert not (checkout.parent / "documents").exists()
    assert not (checkout.parent / "config").exists()


def test_validate_checks_configuration_and_managers_without_deployment(tmp_path, monkeypatch):
    machine = tmp_path / "machines" / "test"
    machine.mkdir(parents=True)
    declaration = machine / "machine.py"
    declaration.write_text("from app.models import Machine\nmanifest = Machine()\n")
    monkeypatch.setattr(env, "ROOT", tmp_path)
    monkeypatch.setattr(env, "config_dir", lambda: tmp_path / "state")
    monkeypatch.setattr(
        info.reporting, "prompt", lambda *a, **kw: pytest.fail("validation prompted")
    )
    checked = []

    def find_executable(name, *, env):
        assert env == {"MC_ID": "test"}
        checked.append(name)
        return name

    monkeypatch.setattr(validation, "find_executable", find_executable)
    runner = CliRunner()
    app = entry._create_app()
    assert runner.invoke(app, ["validate"]).exit_code != 0
    assert runner.invoke(app, ["validate", "-m", "test"]).exit_code == 0
    assert checked
    assert not (tmp_path / "state").exists()

    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "machine").write_text("test\n")
    assert runner.invoke(app, ["validate"]).exit_code == 0
    monkeypatch.setattr(validation, "find_executable", lambda *a, **kw: None)
    result = runner.invoke(app, ["validate"])
    assert isinstance(result.exception, FileNotFoundError)
    declaration.write_text(
        "from app.models import Machine, Package\nmanifest = Machine(packages=[Package()])\n"
    )
    assert runner.invoke(app, ["validate"]).exit_code != 0


@pytest.mark.parametrize("failed_phase", [None, "init_apps.ps1", "files", "packages"])
def test_filtered_deploy_preserves_phases_and_stops_on_failure(monkeypatch, failed_phase) -> None:
    from app import models

    managers = [models.PkgManager.WINGET]
    configuration = models.Configuration(
        pkg_managers=managers,
        modules=["apps"],
        files=[models.FileMapping(source=Path("/source"), target=Path("/target"))],
        scripts=[
            Path("init_apps.ps1"),
            Path("apps.ps1"),
            Path("up_apps.ps1"),
        ],
        packages=[models.Package(name="Example.App", winget="Example.App")],
    )
    configuration.packages[0].selected_source = "winget"
    events = []
    selected_env = {"MC_ID": "test"}
    monkeypatch.setattr(cli, "list_machines", lambda: ["test"])
    configuration.env = selected_env
    monkeypatch.setattr(deploy, "save_machine", lambda machine_id, env: events.append("selected"))

    def load_machine(machine_id, module_names):
        assert machine_id == "test" and module_names == ["apps"]
        events.append("resolved")
        return configuration

    def record(phase):
        events.append(phase)
        if phase == failed_phase:
            raise RuntimeError(f"{phase} failed")

    def setup_managers(declared, *, env, dry_run):
        assert declared == managers and env is selected_env
        record("managers")

    def run_scripts(scripts, *, env, dry_run):
        assert env is selected_env
        for script in scripts:
            record(script.name)

    def install_packages(packages, *, env, dry_run):
        assert env is selected_env
        assert [package.selected_source for package in packages] == ["winget"]
        record("packages")
        return []

    monkeypatch.setattr(deploy, "load_machine", load_machine)
    monkeypatch.setattr(deploy, "deploy_file", lambda mapping, **kwargs: record("files"))
    monkeypatch.setattr(deploy, "setup_managers", setup_managers)
    monkeypatch.setattr(deploy, "run_scripts", run_scripts)
    monkeypatch.setattr(deploy, "install_packages", install_packages)
    expected = [
        "resolved",
        "selected",
        "managers",
        "init_apps.ps1",
        "files",
        "packages",
        "apps.ps1",
    ]
    if failed_phase:
        with pytest.raises(RuntimeError, match=f"{failed_phase} failed"):
            deploy.deploy(machine="test", module_names=["apps"])
        assert events == expected[: expected.index(failed_phase) + 1]
        return

    deploy.deploy(machine="test", module_names=["apps"])
    assert events == expected


def test_preview_uses_requested_machine_without_saving_or_running(tmp_path, monkeypatch):
    # Keep the real loader and environment builder connected to the command.
    monkeypatch.setattr(env, "ROOT", tmp_path)
    env_file = tmp_path / "mc" / "machine"
    env_file.parent.mkdir()
    env_file.write_text("first\n")
    monkeypatch.setattr(env, "config_dir", lambda: env_file.parent)
    machine_dir = tmp_path / "machines" / "second"
    machine_dir.mkdir(parents=True)
    (machine_dir / "config").write_text("new config")
    (machine_dir / "machine.py").write_text(
        "from app.models import Machine, FileMapping, Package\n"
        f"manifest = Machine(env={{'DEV': {str(tmp_path / 'selected')!r}}}, "
        "files=[FileMapping(source='config', target='$DEV/config')], "
        "packages=[Package(name='mc-test-missing-command', cmd='echo selected-env')])\n"
    )
    seen = []
    from app.ops import packages

    def command(cmd, *, env, dry_run, **kwargs):
        assert dry_run
        seen.append(env)
        return None

    monkeypatch.setattr(packages, "run", command)
    result = CliRunner().invoke(entry._create_app(), ["deploy", "-n", "-m", "second"])
    assert result.exit_code == 0, result.exception
    assert seen and seen[0]["MC_ID"] == "second"
    assert seen[0]["DEV"] == str(tmp_path / "selected")
    assert env_file.read_text() == "first\n"
    assert sorted(path.name for path in env_file.parent.iterdir()) == ["machine"]
    assert not (tmp_path / "selected").exists()


def test_upgrade_passes_selected_environment_and_stops_on_failure(monkeypatch):
    from app.models import Configuration

    selected_env = {"MC_ID": "test"}
    configuration = Configuration(
        scripts=[Path("init_setup.py"), Path("setup.py"), Path("up_setup.py")]
    )
    events = []
    monkeypatch.setattr(upgrade, "get_current_machine", lambda: "test")
    configuration.env = selected_env
    monkeypatch.setattr(upgrade, "load_machine", lambda *args, **kwargs: configuration)

    def managers(managers, *, env, dry_run):
        assert env is selected_env and dry_run
        events.append("managers")

    monkeypatch.setattr(upgrade, "upgrade_managers", managers)

    def packages(packages, *, env, dry_run):
        assert env is selected_env and dry_run
        events.append("packages")
        raise RuntimeError("upgrade failed")

    monkeypatch.setattr(upgrade, "upgrade_packages", packages)
    monkeypatch.setattr(upgrade, "run_scripts", lambda *args, **kwargs: events.append("scripts"))
    result = CliRunner().invoke(entry._create_app(), ["upgrade", "--dry-run"])
    assert isinstance(result.exception, RuntimeError)
    assert str(result.exception) == "upgrade failed"
    assert events == ["managers", "packages"]


def test_show_subcommands_skip_configuration_loading(tmp_path, monkeypatch):
    monkeypatch.setattr(info, "get_current_machine", lambda: "saved-machine")
    monkeypatch.setattr(env, "ROOT", tmp_path)
    monkeypatch.setattr(
        info, "load_machine", lambda *a, **kw: pytest.fail("subcommand loaded configuration")
    )
    monkeypatch.setattr(
        info.reporting, "prompt", lambda *a, **kw: pytest.fail("subcommand prompted for a machine")
    )

    app = entry._create_app()
    runner = CliRunner()
    for command, expected in (
        ("id", "saved-machine"),
        ("home", str(tmp_path)),
    ):
        result = runner.invoke(app, ["show", command])
        assert result.exit_code == 0, result.exception
        assert expected in result.output


def test_preview_flag_is_rejected_outside_deployment_commands():
    runner = CliRunner()
    app = entry._create_app()
    for arguments in (
        ["--dry-run", "deploy"],
        ["show", "modules", "--dry-run"],
        ["validate", "--dry-run"],
        ["show", "--dry-run"],
        ["show", "id", "--dry-run"],
    ):
        assert runner.invoke(app, arguments).exit_code == 2
