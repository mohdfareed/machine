"""Checkpoint consistency, failure recovery, and preservation of live data."""

import json
import os
import shutil
import subprocess
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from machines.homelab.backup import state


@pytest.fixture
def homelab(tmp_path, monkeypatch):
    root = tmp_path / "backups"
    root.mkdir(mode=0o700)
    storage = tmp_path / "state"
    media = tmp_path / "media"
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    for name in ("movies", "series", "anime", "downloads"):
        (media / name).mkdir(parents=True)
    monkeypatch.setenv("MC_HOMELAB_BACKUP_DIR", str(root))
    monkeypatch.setenv("MC_HOMELAB_STORAGE_DIR", str(storage))
    monkeypatch.setenv("MC_HOMELAB_MEDIA_DIR", str(media))
    monkeypatch.setenv("MC_HOMELAB_BACKUP_KEEP_LAST", "10")
    monkeypatch.setattr(state, "_checkout", lambda: checkout)
    monkeypatch.setattr(Path, "is_mount", lambda path: path == media)
    monkeypatch.setattr(state, "_local_docker", lambda: None)
    monkeypatch.setattr(state, "_revision", lambda: "a" * 40)
    containers = []
    for number, service in enumerate(("homelab-gateway", "app", "dormant", "watchlist-sync"), 1):
        directory = storage / service
        directory.mkdir(parents=True)
        (directory / "database").write_text("checkpoint data")
        mount = {"Type": "bind", "Source": str(directory), "Destination": "/config", "RW": True}
        if service == "homelab-gateway":
            mount = {"Type": "volume", "Name": "old-gateway", "Destination": "/var/lib/tailscale"}
        containers.append(
            {
                "id": str(number) * 64,
                "image": "sha256:" + ("b" if service == "watchlist-sync" else "a") * 64,
                "service": service,
                "project": "homelab",
                "oneoff": "False",
                "running": service != "dormant",
                "paused": False,
                "restarting": False,
                "exit": 0,
                "mounts": [mount],
            }
        )
    events = []

    def docker(*args):
        events.append(args)
        if args[0] == "ps":
            return "\n".join(item["id"] for item in containers)
        if args[0] == "inspect":
            return "\n".join(json.dumps(item) for item in containers if item["id"] in args)
        if args[:2] == ("image", "inspect"):
            return "sha256:" + "c" * 64
        if args[:2] == ("image", "save"):
            Path(args[3]).write_bytes(b"saved image archive")
            return ""
        if args[:2] == ("volume", "ls"):
            return ""
        if args[:2] in (("volume", "inspect"), ("volume", "create"), ("image", "load")):
            return args[-1]
        if args[0] in ("start", "stop"):
            item = next(item for item in containers if item["id"] == args[-1])
            item["running"] = args[0] == "start"
            return item["id"]
        pytest.fail(f"Unexpected Docker command: {args}")

    def git(*args):
        assert args[0] == "archive"
        with tarfile.open(args[2].removeprefix("--output="), "w"):
            pass
        return ""

    def archive(helper, stage, name, kind, source):
        assert not any(item["running"] for item in containers)
        events.append(("archive", name))
        with tarfile.open(stage / name, "w") as output:
            if kind == "bind":
                output.add(source, arcname=".")

    def extract(helper, extracted, name, kind, target):
        if kind == "bind":
            with tarfile.open(extracted / name) as archive:
                archive.extractall(target, filter="data")

    monkeypatch.setattr(state, "_docker", docker)
    monkeypatch.setattr(state, "_git", git)
    monkeypatch.setattr(state, "_archive", archive)
    monkeypatch.setattr(state, "_extract", extract)
    return SimpleNamespace(
        root=root,
        storage=storage,
        media=media,
        containers=containers,
        events=events,
        docker=docker,
        archive=archive,
    )


@pytest.mark.parametrize("failure", [None, "archive", "forced-stop", "start"])
def test_capture_restarts_only_original_writers_and_keeps_failed_recovery(
    homelab, monkeypatch, failure
):
    original = [item["id"] for item in homelab.containers if item["running"]]
    sync = homelab.containers[-1]["id"]

    def docker(*args):
        if args[0] == "stop":
            record = json.loads((homelab.root / "resume.json").read_text())
            assert set(record["containers"]) == set(original)
        if failure == "start" and args[0] == "start":
            raise subprocess.CalledProcessError(1, args)
        result = homelab.docker(*args)
        if failure == "forced-stop" and args[0] == "stop":
            homelab.containers[-1]["exit"] = 137
        return result

    def archive(*args):
        if failure == "archive" and args[2] == "gateway.tar":
            raise subprocess.CalledProcessError(1, ["docker", "run"])
        homelab.archive(*args)

    monkeypatch.setattr(state, "_docker", docker)
    monkeypatch.setattr(state, "_archive", archive)
    if failure:
        with pytest.raises((subprocess.CalledProcessError, RuntimeError)):
            state.capture()
    else:
        state.capture()
    stops = [event[-1] for event in homelab.events if event[0] == "stop"]
    assert stops[0] == sync
    assert (homelab.root / "resume.json").exists() == (failure == "start")
    if failure == "start":
        monkeypatch.setattr(state, "_docker", homelab.docker)
        state.resume()
    starts = [event[-1] for event in homelab.events if event[0] == "start"]
    assert set(starts) == set(original)
    assert starts[-1] == sync
    assert [item["id"] for item in homelab.containers if item["running"]] == original
    saved = next(event for event in homelab.events if event[:2] == ("image", "save"))
    assert len(saved[4:]) == 3  # Deduplicated runtime images, built sync image, and helper.
    if failure == "forced-stop":
        assert not any(event[0] == "archive" for event in homelab.events)


def test_pending_resume_and_bad_paths_preserve_previous_stage(homelab, monkeypatch):
    stage = homelab.root / "stage"
    stage.mkdir()
    previous = stage / "state.tar"
    previous.write_bytes(b"last checkpoint")
    record = homelab.root / "resume.json"
    record.write_text('{"containers": []}')
    with pytest.raises(RuntimeError, match="Pending writer recovery"):
        state.capture()
    assert record.read_text() == '{"containers": []}'
    record.unlink()
    monkeypatch.setenv("MC_HOMELAB_BACKUP_DIR", str(homelab.storage / "backups"))
    with pytest.raises(ValueError, match="Overlapping"):
        state.capture()
    assert not (homelab.storage / "backups").exists()
    assert previous.read_bytes() == b"last checkpoint"
    assert homelab.events == []


@pytest.mark.parametrize("fail_compose", [False, True])
def test_apply_preserves_current_data_and_stops_partial_start_on_failure(
    homelab, tmp_path, monkeypatch, fail_compose
):
    state.capture()
    extracted = tmp_path / "extracted"
    shutil.copytree(homelab.root / "stage", extracted)
    database = homelab.storage / "app/database"
    database.write_text("new live data")
    homelab.events.clear()

    def compose(command, **kwargs):
        assert "--no-start" in command and "--no-build" in command
        assert command[command.index("--pull") + 1] == "never"
        if fail_compose:
            homelab.containers[1]["running"] = True
            homelab.containers[1]["restarting"] = True
            raise subprocess.CalledProcessError(1, command)
        override = json.loads(Path(command[command.index("up") - 1]).read_text())
        homelab.containers[0]["mounts"][0]["Name"] = override["volumes"]["homelab-gateway-state"][
            "name"
        ]
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(state.subprocess, "run", compose)
    if fail_compose:
        with pytest.raises(subprocess.CalledProcessError):
            state.apply(extracted)
    else:
        state.apply(extracted)
    preserved = list(tmp_path.glob("state.preserved-*"))
    assert len(preserved) == 1
    assert (preserved[0] / "app/database").read_text() == "new live data"
    assert database.read_text() == "checkpoint data"
    assert (extracted / "state.tar").read_bytes() == (homelab.root / "stage/state.tar").read_bytes()
    running = {item["service"] for item in homelab.containers if item["running"]}
    assert running == (set() if fail_compose else {"homelab-gateway", "app", "watchlist-sync"})
    assert not any(event[:2] == ("volume", "rm") for event in homelab.events)
    assert list(homelab.root.glob("restore-*/compose.restore.json"))


def test_apply_refuses_existing_destinations_and_profile_lock(homelab, tmp_path, monkeypatch):
    state.capture()
    extracted = tmp_path / "extracted"
    shutil.copytree(homelab.root / "stage", extracted)
    monkeypatch.setattr(state, "uuid4", lambda: SimpleNamespace(hex="reserved"))
    occupied = tmp_path / "state.restore-reserved"
    occupied.mkdir()
    existing = occupied / "database"
    existing.write_bytes(b"do not overwrite")
    homelab.events.clear()
    with pytest.raises(FileExistsError):
        state.apply(extracted)
    assert existing.read_bytes() == b"do not overwrite"
    assert not any(event[0] in ("start", "stop", "run", "image") for event in homelab.events)
    homelab.events.clear()
    (homelab.root / "profile.lock").touch()
    with pytest.raises(RuntimeError, match="resticprofile is locked"):
        state.apply(extracted)
    assert homelab.events == []
    assert (homelab.storage / "app/database").read_text() == "checkpoint data"


@pytest.mark.skipif(os.name == "nt", reason="Native Unix operation lock")
def test_operation_lock_excludes_overlapping_launcher_or_backup(homelab):
    with state.operation_lock():
        with pytest.raises(RuntimeError, match="operation is active"), state.operation_lock():
            pytest.fail("acquired an active lock")
    with state.operation_lock():
        pass
