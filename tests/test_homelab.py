"""Compose deployment resolves each project's own vault references."""

import subprocess

import pytest
from config.homelab.scripts import services


@pytest.mark.parametrize("has_secrets", [False, True])
def test_project_uses_only_its_own_secret_file(tmp_path, monkeypatch, has_secrets):
    project = tmp_path / "docker" / "example"
    project.mkdir(parents=True)
    (project / "compose.yaml").touch()
    if has_secrets:
        (project / "secrets.env").write_text('TOKEN="op://vault/item/field"\n')
    # Another project's file must not make this project load secrets.
    (project.parent / "secrets.env").touch()
    calls = []

    def run(command, **kwargs):
        assert kwargs == {"cwd": project, "check": True}
        calls.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(services, "__file__", str(tmp_path / "scripts" / "services.py"))
    monkeypatch.setattr(services, "ROOT", tmp_path)
    monkeypatch.setenv("MC_ID", "machine")
    monkeypatch.setattr(services, "_wait_for_docker", lambda: None)
    monkeypatch.setattr(services.subprocess, "run", run)

    services.main()

    prefix = ["docker", "compose"]
    if has_secrets:
        prefix = ["op", "run", "--env-file=secrets.env", "--", *prefix]
    assert calls == [
        [*prefix, "pull", "--ignore-pull-failures"],
        [*prefix, "up", "-d", "--build", "--remove-orphans"],
    ]


@pytest.mark.parametrize("has_secrets", [False, True])
def test_project_stops_on_secret_or_deployment_failure(tmp_path, monkeypatch, has_secrets):
    for name in ("first", "second"):
        project = tmp_path / "docker" / name
        project.mkdir(parents=True)
        (project / "compose.yaml").touch()
        if has_secrets:
            (project / "secrets.env").write_text('TOKEN="op://vault/item/field"\n')
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(services, "__file__", str(tmp_path / "scripts" / "services.py"))
    monkeypatch.setattr(services, "ROOT", tmp_path)
    monkeypatch.setenv("MC_ID", "machine")
    monkeypatch.setattr(services, "_wait_for_docker", lambda: None)
    monkeypatch.setattr(services.subprocess, "run", run)

    with pytest.raises(subprocess.CalledProcessError):
        services.main()

    assert len(calls) == 1
    assert "pull" in calls[0]
