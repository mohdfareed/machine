"""CLI lifecycle regression tests."""

import subprocess

import pytest

from app import cli


def test_sync_abort_stops_before_pull_and_apply(monkeypatch: pytest.MonkeyPatch) -> None:
    """Choosing abort for local changes must end the sync operation."""
    calls: list[list[str]] = []

    def run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout=" M local-change\n", stderr="")

    def unexpected_apply(**_kwargs: object) -> None:
        pytest.fail("sync continued into apply after abort")

    monkeypatch.setattr(cli.settings, "dry_run", False)
    monkeypatch.setattr(cli.subprocess, "run", run)
    monkeypatch.setattr(cli, "_prompt_force", lambda **_kwargs: None)
    monkeypatch.setattr(cli, "apply", unexpected_apply)

    cli.sync(stash=False, force=False, push=False, no_apply=False)

    assert len(calls) == 1
    assert calls[0][-2:] == ["status", "--porcelain"]


@pytest.mark.parametrize("setup_fails", [False, True])
def test_filtered_apply_preserves_declared_manager_setup(monkeypatch, setup_fails) -> None:
    from app import machine as models
    from app.ops import packages as machine_packages

    monkeypatch.setattr(machine_packages, "PLATFORM", machine_packages.Platform.WINDOWS)

    managers = [models.PkgManager.WINGET]
    manifest = models.Machine(pkg_managers=managers, modules=["core", "system", "apps"])
    modules = [
        models.Module(name="core", scripts=["init_pkgs.win.ps1", "core.ps1"]),
        models.Module(name="system", scripts=["init_system.ps1", "system.ps1"]),
        models.Module(
            name="apps", scripts=["init_apps.ps1"], packages=[models.Package(winget="Example.App")]
        ),
    ]
    events = []
    monkeypatch.setattr(models, "load_manifest", lambda *args: manifest)
    monkeypatch.setattr(models, "resolve_modules", lambda *args: modules)
    monkeypatch.setattr(cli, "save_current_machine", lambda *args: None)
    monkeypatch.setattr(cli, "write_env_file", lambda *args: None)
    monkeypatch.setattr(cli, "validate", lambda *args: [])
    monkeypatch.setattr(cli, "filter_scripts", lambda scripts: scripts)
    monkeypatch.setattr(cli, "build_script_env", lambda *args: {})
    monkeypatch.setattr(cli, "cache_sudo", lambda: None)
    monkeypatch.setattr(cli, "deploy_files", lambda *args, **kwargs: (None, []))

    def run_scripts(scripts, *, env, owners):
        assert env["MC_PACKAGE_MANAGERS"] == "winget"
        if scripts[0].startswith("init_"):
            assert scripts == ["init_pkgs.win.ps1", "init_apps.ps1"]
        events.extend(scripts)
        if setup_fails and "init_pkgs.win.ps1" in scripts:
            return [("core", "winget", "setup failed")]
        return []

    def install_packages(packages, declared, **kwargs):
        assert declared == managers
        events.append("packages")
        return []

    monkeypatch.setattr(cli, "run_scripts", run_scripts)
    monkeypatch.setattr(cli, "install_packages", install_packages)
    if setup_fails:
        with pytest.raises(cli.typer.Exit) as exc:
            cli.apply(machine="test", module_names=["apps"])
        assert exc.value.exit_code == 1
        assert events == ["init_pkgs.win.ps1", "init_apps.ps1"]
    else:
        cli.apply(machine="test", module_names=["apps"])
        assert events == ["init_pkgs.win.ps1", "init_apps.ps1", "packages", "core.ps1"]
