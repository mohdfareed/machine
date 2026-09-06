"""CLI lifecycle regression tests."""

import subprocess
from pathlib import Path

import pytest

from machine import cli
from machine import manifest as machine_manifest
from machine.core import Platform
from machine.manifest import FileMapping, MachineManifest, Module, Package


def test_show_hides_non_applicable_files_and_packages(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = Module(
        name="editor",
        files=[
            FileMapping(source=str(tmp_path / "universal"), target="universal-target"),
            FileMapping(
                source=str(tmp_path / "macos"),
                target="macos-target",
                platforms=[Platform.MACOS],
            ),
            FileMapping(
                source=str(tmp_path / "windows"),
                target="windows-target",
                platforms=[Platform.WINDOWS],
            ),
        ],
        packages=[
            Package(name="universal-package", brew="universal-package"),
            Package(
                name="macos-package",
                cask="macos-package",
                platforms=[Platform.MACOS],
            ),
            Package(
                name="windows-package",
                winget="Vendor.WindowsPackage",
                platforms=[Platform.WINDOWS],
            ),
        ],
    )
    output: list[str] = []

    monkeypatch.setattr(cli, "PLATFORM", Platform.MACOS)
    monkeypatch.setattr(cli.settings, "home", tmp_path)
    monkeypatch.setattr(
        machine_manifest,
        "load_manifest",
        lambda _machine, _root: MachineManifest(modules=["editor"]),
    )
    monkeypatch.setattr(machine_manifest, "resolve_modules", lambda _modules, _root: [module])
    monkeypatch.setattr(
        cli.console,
        "print",
        lambda *values, **_kwargs: output.append(" ".join(str(value) for value in values)),
    )

    cli.show(machine="test")

    rendered = "\n".join(output)
    assert "universal-target" in rendered
    assert "macos-target" in rendered
    assert "windows-target" not in rendered
    assert "universal-package" in rendered
    assert "macos-package" in rendered
    assert "windows-package" not in rendered


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
