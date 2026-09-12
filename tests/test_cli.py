"""CLI lifecycle regression tests."""

import os
import subprocess
from pathlib import Path

import pytest

from app.cli import deploy, entry, sync


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
    monkeypatch.setattr(sync.settings, "home", checkout)
    monkeypatch.setattr(sync.settings, "dry_run", False)
    monkeypatch.setattr(sync, "_CANONICAL_REPO_URL", str(canonical))
    monkeypatch.setattr(sync, "get_current_machine", lambda: "test")
    deployed = []
    monkeypatch.setattr(sync, "deploy", lambda **kwargs: deployed.append(kwargs))
    return canonical, checkout, deployed


def test_machine_validation_is_case_insensitive(monkeypatch):
    monkeypatch.setattr(entry, "machine_ids", ["homelab", "macbook"])

    assert entry.validate_machine("HOMELAB") == "homelab"
    with pytest.raises(entry.typer.BadParameter):
        entry.validate_machine("unknown")


@pytest.mark.parametrize("no_deploy", [False, True])
def test_sync_restores_local_edits_before_deploy(sync_repos, monkeypatch, no_deploy):
    canonical, checkout, deployed = sync_repos

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
        sync, "deploy", lambda **kwargs: deployed.append((checkout / "config.txt").read_text())
    )
    sync.sync(no_deploy=no_deploy)

    assert git(checkout, "rev-parse", "HEAD") == git(canonical, "rev-parse", "HEAD")
    assert (checkout / "config.txt").read_text() == expected
    assert deployed == ([] if no_deploy else [expected])


def test_sync_autostash_conflict_preserves_edits_and_stops_deploy(sync_repos):
    canonical, checkout, deployed = sync_repos
    (checkout / "config.txt").write_text("local edit\n")
    (canonical / "config.txt").write_text("upstream edit\n")
    git(canonical, "commit", "-am", "Update config")

    with pytest.raises(SystemExit):
        sync.sync(no_deploy=False)

    assert git(checkout, "ls-files", "--unmerged")
    assert git(checkout, "show", "stash@{0}:config.txt") == "local edit"
    assert not deployed


def test_sync_divergence_preserves_commits_and_stops_deploy(sync_repos):
    canonical, checkout, deployed = sync_repos
    (checkout / "config.txt").write_text("local commit\n")
    git(checkout, "commit", "-am", "Local change")
    before = git(checkout, "rev-parse", "HEAD")
    (canonical / "config.txt").write_text("upstream commit\n")
    git(canonical, "commit", "-am", "Upstream change")

    with pytest.raises(SystemExit):
        sync.sync(no_deploy=False)

    assert git(checkout, "rev-parse", "HEAD") == before
    assert not deployed


def test_sync_fetch_failure_does_not_deploy_stale_fetch_head(sync_repos, monkeypatch):
    canonical, checkout, deployed = sync_repos
    git(checkout, "fetch", str(canonical), "main")
    before = git(checkout, "rev-parse", "HEAD")
    monkeypatch.setattr(sync, "_CANONICAL_REPO_URL", str(canonical / "missing"))

    with pytest.raises(SystemExit):
        sync.sync(no_deploy=False)

    assert git(checkout, "rev-parse", "HEAD") == before
    assert not deployed


def test_sync_dry_run_does_not_fetch_or_deploy(sync_repos, monkeypatch):
    _, checkout, deployed = sync_repos
    monkeypatch.setattr(sync.settings, "dry_run", True)
    sync.sync(no_deploy=False)
    assert not (checkout / ".git" / "FETCH_HEAD").exists()
    assert not deployed


@pytest.mark.parametrize("setup_fails", [False, True])
def test_filtered_deploy_preserves_declared_manager_setup(monkeypatch, setup_fails) -> None:
    from app import machine, models
    from app.ops import managers as machine_managers

    monkeypatch.setattr(machine_managers, "PLATFORM", models.Platform.WINDOWS)

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
    monkeypatch.setattr(machine, "load_machine", lambda *args: (manifest, modules))
    monkeypatch.setattr(deploy, "save_current_machine", lambda *args: None)
    monkeypatch.setattr(deploy, "write_env_file", lambda *args: None)

    monkeypatch.setattr(deploy, "filter_scripts", lambda scripts: scripts)
    monkeypatch.setattr(deploy, "build_env", lambda *args: {})
    monkeypatch.setattr(deploy, "cache_sudo", lambda: None)
    monkeypatch.setattr(
        deploy, "deploy_files", lambda *args, **kwargs: models.FileResult(created=0, failures=[])
    )

    def run_scripts(scripts, *, env, owners):
        assert env["MC_PACKAGE_MANAGERS"] == "winget"
        if scripts[0].startswith("init_"):
            assert scripts == ["init_pkgs.win.ps1", "init_apps.ps1"]
        events.extend(scripts)
        if setup_fails and "init_pkgs.win.ps1" in scripts:
            return [models.Failure(module="core", item="winget", detail="setup failed")]
        return []

    def install_packages(packages, declared, **kwargs):
        assert declared == managers
        events.append("packages")
        return []

    monkeypatch.setattr(deploy, "run_scripts", run_scripts)
    monkeypatch.setattr(deploy, "install_packages", install_packages)
    if setup_fails:
        with pytest.raises(deploy.typer.Exit) as exc:
            deploy.deploy(machine="test", module_names=["apps"])
        assert exc.value.exit_code == 1
        assert events == ["init_pkgs.win.ps1", "init_apps.ps1"]
    else:
        deploy.deploy(machine="test", module_names=["apps"])
        assert events == ["init_pkgs.win.ps1", "init_apps.ps1", "packages", "core.ps1"]
