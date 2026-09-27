"""Homelab deployment commands and failure handling."""

import importlib.util
import subprocess
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "homelab_services", _ROOT / "machines/homelab/scripts/services.mac.py"
)
assert _spec is not None and _spec.loader is not None
services = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(services)


@pytest.mark.parametrize("fail_pull", [False, True])
def test_compose_uses_vault_references_and_stops_on_failure(tmp_path, monkeypatch, fail_pull):
    project = tmp_path / "docker"
    project.mkdir()
    media = tmp_path / "media"
    for name in ("movies", "series", "anime", "downloads"):
        (media / name).mkdir(parents=True)
    monkeypatch.setenv("MC_HOMELAB_MEDIA_DIR", str(media))
    monkeypatch.setenv("MC_HOMELAB_STORAGE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr(Path, "is_mount", lambda path: path == media)
    monkeypatch.setattr(services, "__file__", str(tmp_path / "scripts/services.mac.py"))
    monkeypatch.setattr(services, "_wait_for_docker", lambda: None)
    calls = []

    def run(command, **kwargs):
        assert kwargs == {"cwd": project, "check": True}
        calls.append(command)
        if fail_pull:
            raise subprocess.CalledProcessError(1, command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(services.subprocess, "run", run)
    if fail_pull:
        with pytest.raises(subprocess.CalledProcessError):
            services.main()
    else:
        services.main()

    prefix = ["op", "run", "--env-file=secrets.env", "--", "docker", "compose"]
    expected = [[*prefix, "pull", "--ignore-pull-failures"]]
    if not fail_pull:
        expected.append([*prefix, "up", "-d", "--build", "--remove-orphans"])
    assert calls == expected
    assert (tmp_path / "state").is_dir()
    assert not list((tmp_path / "state").iterdir())
