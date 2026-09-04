"""CLI lifecycle regression tests."""

import subprocess

import pytest

from machine import cli


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
