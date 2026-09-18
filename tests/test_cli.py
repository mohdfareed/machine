"""CLI lifecycle regression tests."""

import os
import subprocess
from pathlib import Path

import pytest
import typer
from app import cli, env
from app.cli import deploy, entry, info, sync, upgrade
from typer.testing import CliRunner


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
    monkeypatch.setattr(sync, "user_documents_path", lambda: tmp_path / "documents")

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
    original_query = sync.query

    def query(cmd, **kwargs):
        if cmd[:4] == ["uv", "tool", "dir", "--bin"]:
            return subprocess.CompletedProcess(cmd, 0, stdout=str(tmp_path / "tool bin"))
        executable = tmp_path / "tool bin" / (cli.COMMAND + (".exe" if env.is_windows else ""))
        if cmd == [str(executable)]:
            scripts = {
                "source_zsh": "\n#compdef mc\n",
                "source_powershell": "Register-ArgumentCompleter -Native -CommandName mc\n",
            }
            return subprocess.CompletedProcess(
                cmd, 0, stdout=scripts[kwargs["env"]["_MC_COMPLETE"]]
            )
        return original_query(cmd, **kwargs)

    monkeypatch.setattr(sync, "query", query)
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
    env_file = tmp_path / ".env"
    monkeypatch.setattr(env, "_ENV_FILE", env_file)
    monkeypatch.setenv("MC_ID", "stale")
    monkeypatch.setattr(cli, "list_machines", lambda: ["first", "second"])
    monkeypatch.setattr(info, "list_machines", lambda: ["first", "second"])
    monkeypatch.setattr(deploy, "list_machines", lambda: ["first", "second"])
    monkeypatch.setattr(env, "ROOT", tmp_path)
    selected = []

    def load_machine(machine_id, module_names=None, *, env):
        selected.append(machine_id)
        raise RuntimeError("Stop before deployment")

    monkeypatch.setattr(deploy, "load_machine", load_machine)
    monkeypatch.setattr(info, "load_machine", load_machine)
    persisted = []
    monkeypatch.setattr(deploy, "set_current_machine", persisted.append)
    app = entry._create_app()
    runner = CliRunner()

    # A new machine can be selected, then a changed file supplies the next default.
    result = runner.invoke(app, [command], input="FIRST\n")
    assert isinstance(result.exception, RuntimeError)
    env_file.write_text("MC_ID=second\n")
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
    completion = Path.home() / ".zsh/completions/_mc"
    if env.is_windows:
        assert not completion.exists()
    else:
        assert completion.read_text() == "#compdef mc\n"
    powershell_dir = (
        canonical.parent / "documents/PowerShell"
        if windows
        else canonical.parent / "config/powershell"
    )
    assert (powershell_dir / "completions/mc.ps1").read_text() == (
        "Register-ArgumentCompleter -Native -CommandName mc\n"
    )


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
    assert not (Path.home() / ".zsh/completions/_mc").exists()
    assert not (checkout.parent / "documents").exists()
    assert not (checkout.parent / "config").exists()


def test_sync_completion_failure_preserves_existing_file(sync_repos, monkeypatch):
    _, checkout = sync_repos
    monkeypatch.setattr(env, "is_windows", False)
    completion = checkout.parent / "config/powershell/completions/mc.ps1"
    completion.parent.mkdir(parents=True)
    completion.write_text("existing completion\n")
    original_query = sync.query

    def query(cmd, **kwargs):
        if "_MC_COMPLETE" in kwargs["env"]:
            raise RuntimeError("Completion generation failed")
        return original_query(cmd, **kwargs)

    monkeypatch.setattr(sync, "query", query)
    with pytest.raises(RuntimeError, match="Completion generation failed"):
        sync.sync()
    assert completion.read_text() == "existing completion\n"


@pytest.mark.parametrize("failed_phase", [None, "preflight", "packages"])
def test_filtered_deploy_preserves_phases_and_stops_on_failure(monkeypatch, failed_phase) -> None:
    from app import models

    managers = [models.PkgManager.WINGET]
    configuration = models.Machine(
        pkg_managers=managers,
        modules=["apps"],
        files=[models.FileMapping(source=Path("/source"), target=Path("/target"))],
        scripts=[Path("init_apps.ps1"), Path("apps.ps1"), Path("up_apps.ps1")],
        packages=[models.Package(name="Example.App", winget="Example.App")],
    )
    configuration.packages[0].selected_source = "winget"
    events = []
    selected_env = {"MC_ID": "test"}
    monkeypatch.setattr(cli, "list_machines", lambda: ["test"])
    monkeypatch.setattr(deploy, "build_env", lambda machine_id: selected_env)
    monkeypatch.setattr(deploy, "set_current_machine", lambda machine_id: events.append("selected"))

    def load_machine(machine_id, module_names, *, env):
        assert machine_id == "test" and module_names == ["apps"]
        assert env is selected_env
        events.append("validated")
        return configuration

    def record(phase):
        events.append(phase)
        if phase == failed_phase:
            raise RuntimeError(f"{phase} failed")

    def validate_managers(declared, *, env):
        assert declared == managers and env is selected_env
        record("preflight")

    def setup_managers(declared, *, env, dry_run):
        assert declared == managers and env is selected_env
        record("managers")

    def run_scripts(scripts, *, env, dry_run):
        assert env is selected_env
        events.extend(script.name for script in scripts)

    def install_packages(packages, *, env, dry_run, reporter):
        assert env is selected_env
        assert [package.selected_source for package in packages] == ["winget"]
        record("packages")
        return []

    monkeypatch.setattr(deploy, "load_machine", load_machine)
    monkeypatch.setattr(deploy, "validate_managers", validate_managers)
    monkeypatch.setattr(deploy, "deploy_file", lambda mapping, **kwargs: record("files"))
    monkeypatch.setattr(deploy, "setup_managers", setup_managers)
    monkeypatch.setattr(deploy, "run_scripts", run_scripts)
    monkeypatch.setattr(deploy, "install_packages", install_packages)
    expected = [
        "validated",
        "preflight",
        "selected",
        "files",
        "managers",
        "init_apps.ps1",
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
    env_file = tmp_path / ".env"
    env_file.write_text("MC_ID=first\n")
    monkeypatch.setattr(env, "_ENV_FILE", env_file)
    machine_dir = tmp_path / "machines" / "second"
    machine_dir.mkdir(parents=True)
    (machine_dir / "config").write_text("new config")
    (machine_dir / "machine.env").write_text(f"DEV={tmp_path / 'selected'}\n")
    (machine_dir / "machine.py").write_text(
        "from app.models import Machine, FileMapping, Package\n"
        "manifest = Machine(files=[FileMapping(source='config', target='$DEV/config')], "
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
    assert env_file.read_text() == "MC_ID=first\n"
    assert not (tmp_path / "selected").exists()


def test_upgrade_passes_selected_environment_and_stops_on_failure(monkeypatch):
    from app.models import Machine

    selected_env = {"MC_ID": "test"}
    configuration = Machine(scripts=[Path("init_setup.py"), Path("setup.py"), Path("up_setup.py")])
    events = []
    monkeypatch.setattr(upgrade, "get_current_machine", lambda: "test")
    monkeypatch.setattr(upgrade, "build_env", lambda machine_id: selected_env)
    monkeypatch.setattr(upgrade, "load_machine", lambda *args, **kwargs: configuration)
    monkeypatch.setattr(upgrade, "validate_managers", lambda *args, **kwargs: None)

    def managers(managers, *, env, dry_run):
        assert env is selected_env and dry_run
        events.append("managers")

    monkeypatch.setattr(upgrade, "upgrade_managers", managers)

    def packages(packages, *, env, dry_run, reporter):
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

    def build_env(machine_id, *, include_private):
        assert machine_id == "saved-machine" and not include_private
        return {"MC_PRIVATE": str(tmp_path / "private")}

    monkeypatch.setattr(info, "build_env", build_env)
    app = entry._create_app()
    runner = CliRunner()
    for command, expected in (
        ("id", "saved-machine"),
        ("home", str(tmp_path)),
        ("private", str(tmp_path / "private")),
        ("status", "saved-machine"),
    ):
        result = runner.invoke(app, ["show", command])
        assert result.exit_code == 0, result.exception
        assert expected in result.output


def test_preview_flag_is_rejected_outside_deployment_commands():
    runner = CliRunner()
    app = entry._create_app()
    for arguments in (
        ["--dry-run", "deploy"],
        ["list", "--dry-run"],
        ["show", "--dry-run"],
        ["show", "id", "--dry-run"],
    ):
        assert runner.invoke(app, arguments).exit_code == 2
