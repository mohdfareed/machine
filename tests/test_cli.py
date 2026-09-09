"""CLI lifecycle regression tests."""

import os
import subprocess
from pathlib import Path

import pytest

from app import cli


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def sync_repos(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Exercise real Git history without user identities, hooks, or network access.
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
    monkeypatch.setattr(cli.settings, "home", checkout)
    monkeypatch.setattr(cli.settings, "dry_run", False)
    monkeypatch.setattr(cli, "CANONICAL_REPO_URL", str(canonical))
    monkeypatch.setattr(cli, "get_current_machine", lambda: "test")
    applied = []
    monkeypatch.setattr(cli, "apply", lambda **kwargs: applied.append(kwargs))
    return canonical, checkout, applied


@pytest.mark.parametrize("no_apply", [False, True])
def test_sync_restores_local_edits_before_apply(sync_repos, monkeypatch, no_apply):
    canonical, checkout, applied = sync_repos

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

    # Observe the restored content at deployment time, not just after sync returns.
    monkeypatch.setattr(
        cli, "apply", lambda **kwargs: applied.append((checkout / "config.txt").read_text())
    )
    cli.sync(no_apply=no_apply)

    assert git(checkout, "rev-parse", "HEAD") == git(canonical, "rev-parse", "HEAD")
    assert (checkout / "config.txt").read_text() == expected
    assert applied == ([] if no_apply else [expected])


def test_sync_autostash_conflict_preserves_edits_and_stops_apply(sync_repos):
    canonical, checkout, applied = sync_repos
    (checkout / "config.txt").write_text("local edit\n")
    (canonical / "config.txt").write_text("upstream edit\n")
    git(canonical, "commit", "-am", "Update config")

    with pytest.raises(SystemExit):
        cli.sync(no_apply=False)

    assert git(checkout, "ls-files", "--unmerged")
    assert git(checkout, "show", "stash@{0}:config.txt") == "local edit"
    assert not applied


def test_sync_divergence_preserves_commits_and_stops_apply(sync_repos):
    canonical, checkout, applied = sync_repos
    (checkout / "config.txt").write_text("local commit\n")
    git(checkout, "commit", "-am", "Local change")
    before = git(checkout, "rev-parse", "HEAD")
    (canonical / "config.txt").write_text("upstream commit\n")
    git(canonical, "commit", "-am", "Upstream change")

    with pytest.raises(SystemExit):
        cli.sync(no_apply=False)

    assert git(checkout, "rev-parse", "HEAD") == before
    assert not applied


def test_sync_fetch_failure_does_not_apply_stale_fetch_head(sync_repos, monkeypatch):
    canonical, checkout, applied = sync_repos
    git(checkout, "fetch", str(canonical), "main")
    before = git(checkout, "rev-parse", "HEAD")
    monkeypatch.setattr(cli, "CANONICAL_REPO_URL", str(canonical / "missing"))

    with pytest.raises(SystemExit):
        cli.sync(no_apply=False)

    assert git(checkout, "rev-parse", "HEAD") == before
    assert not applied


def test_sync_dry_run_does_not_fetch_or_apply(sync_repos, monkeypatch):
    _, checkout, applied = sync_repos
    monkeypatch.setattr(cli.settings, "dry_run", True)
    cli.sync(no_apply=False)
    assert not (checkout / ".git" / "FETCH_HEAD").exists()
    assert not applied


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
