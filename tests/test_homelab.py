"""Homelab deployment commands and failure handling."""

import importlib.util
import subprocess
from contextlib import nullcontext
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "homelab_services", _ROOT / "machines/homelab/scripts/services.mac.py"
)
assert _spec is not None and _spec.loader is not None
services = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(services)


@pytest.fixture(autouse=True)
def _unlocked_operations(monkeypatch):
    monkeypatch.setattr(services, "_operation_lock", nullcontext)


@pytest.mark.parametrize("fail_pull", [False, True])
def test_compose_uses_vault_references_and_stops_on_failure(tmp_path, monkeypatch, fail_pull):
    project = tmp_path / "docker"
    project.mkdir()
    media = tmp_path / "media"
    for name in ("movies", "series", "anime", "downloads"):
        (media / name).mkdir(parents=True)
    existing_media = media / "movies" / "existing.mkv"
    existing_media.write_bytes(b"existing media")
    monkeypatch.setenv("MC_HOMELAB_MEDIA_DIR", str(media))
    monkeypatch.setenv("MC_HOMELAB_STORAGE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr(Path, "is_mount", lambda path: path == media)
    monkeypatch.setattr(services, "__file__", str(tmp_path / "scripts/services.mac.py"))
    monkeypatch.setattr(services, "_wait_for_docker", lambda: None)
    calls = []

    def run(command, **kwargs):
        assert kwargs["cwd"] == project
        assert kwargs["check"] is True
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
    assert existing_media.read_bytes() == b"existing media"


@pytest.mark.parametrize("mounted", [False, True], ids=["unmounted-share", "missing-media-folders"])
def test_unready_media_stops_before_creating_state_or_starting_services(
    tmp_path, monkeypatch, mounted
):
    media = tmp_path / "media"
    media.mkdir()
    if not mounted:
        for name in ("movies", "series", "anime", "downloads"):
            (media / name).mkdir()
    state = tmp_path / "state"
    monkeypatch.setenv("MC_HOMELAB_MEDIA_DIR", str(media))
    monkeypatch.setenv("MC_HOMELAB_STORAGE_DIR", str(state))
    monkeypatch.setattr(Path, "is_mount", lambda path: mounted)
    monkeypatch.setattr(
        services,
        "_wait_for_docker",
        lambda: pytest.fail("started services before checking media storage"),
    )
    with pytest.raises(FileNotFoundError):
        services.main()
    assert not state.exists()
