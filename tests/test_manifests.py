"""Manifest dependency and override behavior tests."""

from pathlib import Path

from app.core import Platform
from app.machine import FileMapping, Package, load_manifest
from app.ops import packages as machine_packages
from app.ops import scripts as machine_scripts


def test_module_dependencies_auto_included(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    machine_dir = tmp_path / "machines" / "test"
    machine_dir.mkdir(parents=True)
    for name, dependencies in {
        "core": [],
        "base": [],
        "client": ["base"],
        "server": ["client"],
    }.items():
        (config_dir / f"{name}.py").write_text(
            f"from app.machine import Module\nmodule = Module(depends={dependencies!r})\n",
            encoding="utf-8",
        )
    (machine_dir / "manifest.py").write_text(
        "from app.machine import Machine\nmanifest = Machine(modules=['server', 'client'])\n",
        encoding="utf-8",
    )

    manifest = load_manifest("test", tmp_path)

    assert manifest.modules == ["core", "base", "client", "server"]


def test_manifest_override_preserves_metadata(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "core.py").write_text("from app.machine import Module\nmodule = Module()\n")
    (config_dir / "example.py").write_text(
        "from app.core import Platform\n"
        "from app.machine import FileMapping, Module\n"
        "module = Module(overrides=[FileMapping(\n"
        "    source='local.conf', target='~/.example/config',\n"
        "    mode=0o600, platforms=[Platform.LINUX, Platform.WINDOWS],\n"
        ")])\n",
        encoding="utf-8",
    )
    machine_dir = tmp_path / "machines" / "test"
    machine_dir.mkdir(parents=True)
    (machine_dir / "manifest.py").write_text(
        "from app.machine import Machine\nmanifest = Machine(modules=['example'])\n",
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


def test_core_is_included_with_or_without_manager_declarations(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "core.py").write_text("from app.machine import Module\nmodule = Module()\n")
    (config_dir / "apps.py").write_text(
        "from app.machine import Module, Package\n"
        "module = Module(packages=[Package(winget='Example.App')])\n"
    )
    machines_dir = tmp_path / "machines"
    machines_dir.mkdir()
    (machines_dir / "empty.py").write_text(
        "from app.machine import Machine\nmanifest = Machine(modules=['apps'])\n"
    )
    (machines_dir / "declared.py").write_text(
        "from app.machine import Machine, Package, PkgManager\n"
        "manifest = Machine(pkg_managers=[PkgManager.WINGET], "
        "packages=[Package(winget='Example.App')])\n"
    )
    assert load_manifest("empty", tmp_path).modules == ["core", "apps"]
    assert load_manifest("declared", tmp_path).modules == ["core"]


def test_platform_matching_is_directional_and_shared(monkeypatch) -> None:
    expected = {
        Platform.MACOS: {Platform.MACOS, Platform.UNIX},
        Platform.LINUX: {Platform.LINUX, Platform.UNIX},
        Platform.WSL: {Platform.WSL, Platform.LINUX, Platform.UNIX},
        Platform.WINDOWS: {Platform.WINDOWS},
        Platform.UNIX: {Platform.UNIX},
    }
    for platform, matches in expected.items():
        monkeypatch.setattr(machine_scripts, "PLATFORM", platform)
        for target in Platform:
            assert platform.is_a(target) == (target in matches)
            file = FileMapping(source="source", target="target", platforms=[target])
            package = Package(name="example", brew="example", platforms=[target])
            assert file.applies_to(platform) == (target in matches)
            assert package.applies_to(platform) == (target in matches)
            tag = "win" if target == Platform.WINDOWS else target.value
            assert machine_scripts.matches_platform(Path(f"setup.{tag}.sh")) == (target in matches)
        assert FileMapping(source="source", target="target").applies_to(platform)
        assert not FileMapping(source="source", target="target", platforms=[]).applies_to(platform)
        assert machine_scripts.matches_platform(Path("setup.sh"))

    monkeypatch.setattr(machine_packages, "PLATFORM", Platform.WSL)
    assert machine_packages._applicable_sources(Package(apt="example", snap="example")) == [
        "apt",
        "snap",
    ]


def test_nested_modules_discovery_and_resolution(tmp_path: Path) -> None:
    from app.machine import list_modules, load_module

    config = tmp_path / "config"
    for name in ["core", "tools/base", "tools/editor", "other/editor", "tools/editor/assets"]:
        directory = config / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "module.py").write_text("from app.machine import Module\nmodule = Module()\n")
    editor = config / "tools" / "editor"
    (editor / "module.py").write_text(
        "from app.machine import Module, FileMapping\n"
        "module = Module(depends=['tools.base'], "
        "files=[FileMapping(source='settings.json', target='~/.editor.json')])\n"
    )
    (editor / "scripts").mkdir()
    script = editor / "scripts" / "init_editor.unix.sh"
    script.write_text("#!/bin/sh\n")
    machines = tmp_path / "machines"
    machines.mkdir()
    (machines / "test.py").write_text(
        "from app.machine import Machine\nmanifest = Machine(modules=['tools.editor'])\n"
    )

    assert list_modules(tmp_path) == ["core", "other.editor", "tools.base", "tools.editor"]
    assert load_manifest("test", tmp_path).modules == ["core", "tools.base", "tools.editor"]
    module = load_module("tools.editor", tmp_path)
    assert module.name == "tools.editor"
    assert module.files[0].source == str(editor / "settings.json")
    assert module.scripts == [str(script)]


def test_init_scripts_refresh_path_and_stop_on_failure(monkeypatch) -> None:
    events = []
    monkeypatch.setattr(machine_scripts, "_load_state", lambda: {})
    monkeypatch.setattr(machine_scripts, "_save_state", lambda state: None)
    monkeypatch.setattr(machine_scripts.settings, "dry_run", False)
    monkeypatch.setattr(machine_scripts, "refresh_path", lambda: events.append("path"))

    def execute(script, env, module):
        events.append(script.name)
        if script.name == "init_failed.sh":
            return (module, str(script), "failed")
        return None

    monkeypatch.setattr(machine_scripts, "_execute", execute)
    failures = machine_scripts.run_scripts(["init_first.sh", "init_failed.sh", "init_last.sh"])
    assert events == ["init_first.sh", "path", "init_failed.sh"]
    assert failures == [("?", "init_failed.sh", "failed")]
