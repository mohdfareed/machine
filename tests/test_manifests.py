"""Manifest dependency and override behavior tests."""

from pathlib import Path

from machine.core import Platform
from machine.manifest import load_manifest


def test_module_dependencies_auto_included(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    machine_dir = tmp_path / "machines" / "test"
    machine_dir.mkdir(parents=True)
    for name, dependencies in {
        "base": [],
        "client": ["base"],
        "server": ["client"],
    }.items():
        (config_dir / f"{name}.py").write_text(
            f"from machine.manifest import Module\nmodule = Module(depends={dependencies!r})\n",
            encoding="utf-8",
        )
    (machine_dir / "manifest.py").write_text(
        "from machine.manifest import MachineManifest\n"
        "manifest = MachineManifest(modules=['server', 'client'])\n",
        encoding="utf-8",
    )

    manifest = load_manifest("test", tmp_path)

    assert manifest.modules == ["base", "client", "server"]


def test_manifest_override_preserves_metadata(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "example.py").write_text(
        "from machine.core import Platform\n"
        "from machine.manifest import FileMapping, Module\n"
        "module = Module(overrides=[FileMapping(\n"
        "    source='local.conf', target='~/.example/config',\n"
        "    mode=0o600, platforms=[Platform.LINUX, Platform.WINDOWS],\n"
        ")])\n",
        encoding="utf-8",
    )
    machine_dir = tmp_path / "machines" / "test"
    machine_dir.mkdir(parents=True)
    (machine_dir / "manifest.py").write_text(
        "from machine.manifest import MachineManifest\n"
        "manifest = MachineManifest(modules=['example'])\n",
        encoding="utf-8",
    )
    local_config = machine_dir / "local.conf"
    local_config.write_text("local settings", encoding="utf-8")

    manifest = load_manifest("test", tmp_path)

    assert len(manifest.files) == 1
    override = manifest.files[0]
    assert override.source == str(local_config)
    assert override.target == "~/.example/config"
    assert override.mode == 0o600
    assert override.platforms == [Platform.LINUX, Platform.WINDOWS]
