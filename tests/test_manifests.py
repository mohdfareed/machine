"""Manifest dependency and override behavior tests."""

from inspect import signature
from pathlib import Path

import pytest
from pydantic import ValidationError

from app import env as machine_env
from app import machine as machine_loader
from app.discovery import list_machines, list_modules
from app.machine import load_machine
from app.models import FileMapping, Package, PkgManager, Platform


@pytest.fixture
def selected_env(tmp_path: Path) -> dict[str, str]:
    return {
        "HOME": str(tmp_path / "home"),
        "USERPROFILE": str(tmp_path / "home"),
        "APPDATA": str(tmp_path / "app-data"),
        "LOCALAPPDATA": str(tmp_path / "local-app-data"),
    }


def test_all_manifests_load(monkeypatch, selected_env) -> None:
    platforms = {
        "pc": [Platform.WINDOWS, Platform.WSL],
        "gleason": [Platform.WINDOWS, Platform.WSL],
        "homelab": [Platform.MACOS],
        "macbook": [Platform.MACOS],
    }
    for machine_id in list_machines():
        for platform in platforms[machine_id]:
            monkeypatch.setattr(machine_env, "PLATFORM", platform)
            load_machine(machine_id, env=selected_env)


def test_load_machine_validates_only_applicable_selected_sources(
    monkeypatch, tmp_path: Path, selected_env
) -> None:
    monkeypatch.setattr(machine_env, "ROOT", tmp_path)
    monkeypatch.setattr(machine_env, "PLATFORM", Platform.MACOS)
    selected = tmp_path / "config" / "selected"
    selected.mkdir(parents=True)
    (selected / "module.py").write_text(
        "from app.models import FileMapping, Module, Platform\n"
        "module = Module(files=[\n"
        "    FileMapping(source='settings.conf', target='~/.config'),\n"
        "    FileMapping(source='missing.conf', target='$UNDEFINED/config', "
        "platforms=[Platform.WINDOWS]),\n"
        "], scripts=['missing.win.ps1', '_helper.py'])\n"
    )
    source = selected / "settings.conf"
    source.write_text("settings\n")
    other = tmp_path / "config" / "other"
    other.mkdir()
    (other / "module.py").write_text(
        "from app.models import FileMapping, Module\n"
        "module = Module(files=[FileMapping(source='missing.conf', target='~/.other')])\n"
    )
    machine = tmp_path / "machines" / "test"
    machine.mkdir(parents=True)
    (machine / "machine.py").write_text(
        "from app.models import Machine\n"
        "manifest = Machine(modules=['selected', 'other'], scripts=['missing.sh'])\n"
    )

    configuration = load_machine("test", ["selected"], env=selected_env)
    assert [file.source for file in configuration.files] == [str(source)]
    assert configuration.scripts == []

    source.unlink()
    with pytest.raises(ValueError, match="File source missing"):
        load_machine("test", ["selected"], env=selected_env)


@pytest.mark.parametrize("cycle", [False, True], ids=["dependencies", "dependency-cycle"])
def test_module_dependencies_loaded_once(monkeypatch, tmp_path: Path, cycle, selected_env) -> None:
    monkeypatch.setattr(machine_env, "ROOT", tmp_path)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    machine_dir = tmp_path / "machines" / "test"
    machine_dir.mkdir(parents=True)
    for name, dependencies in {
        "core": [],
        "base": ["server"] if cycle else [],
        "client": ["base"],
        "server": ["client"],
    }.items():
        (config_dir / name).mkdir()
        (config_dir / name / "module.py").write_text(
            f"from app.models import Module\nmodule = Module(depends={dependencies!r})\n",
            encoding="utf-8",
        )
    (machine_dir / "machine.py").write_text(
        """
from app.models import Machine
manifest = Machine(modules=['server', 'client'])
""",
        encoding="utf-8",
    )

    imported = []
    import_py = machine_loader._import_py

    def record_import(path):
        imported.append(path)
        return import_py(path)

    monkeypatch.setattr(machine_loader, "_import_py", record_import)
    if cycle:
        with pytest.raises(ValueError):
            load_machine("test", env=selected_env)
    else:
        manifest = load_machine("test", env=selected_env)
        assert manifest.modules == ["base", "client", "server"]

    assert len(imported) == len(set(imported)) == 4


@pytest.mark.parametrize("explicit", [False, True], ids=["module-override", "explicit-mapping"])
def test_manifest_override_preserves_metadata(
    monkeypatch, tmp_path: Path, explicit, selected_env
) -> None:
    monkeypatch.setattr(machine_env, "ROOT", tmp_path)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "example").mkdir()
    (config_dir / "example" / "module.py").write_text(
        "from app.models import FileMapping, Module, Platform\n"
        "module = Module(overrides=[FileMapping(\n"
        "    source='local.conf', target='~/.example/config',\n"
        "    mode=0o600, platforms=[Platform.UNIX, Platform.WINDOWS],\n"
        ")])\n",
        encoding="utf-8",
    )
    machine_dir = tmp_path / "machines" / "test"
    machine_dir.mkdir(parents=True)
    explicit_mapping = (
        "FileMapping(source='explicit.conf', target='~/.example/config', "
        "mode=0o600, platforms=[Platform.UNIX, Platform.WINDOWS])"
        if explicit
        else ""
    )
    (machine_dir / "machine.py").write_text(
        "from app.models import FileMapping, Machine, PkgManager, Platform\n"
        "manifest = Machine(modules=['example'], pkg_managers=[PkgManager.BREW], "
        f"files=[{explicit_mapping}])\n",
        encoding="utf-8",
    )
    local_config = machine_dir / "local.conf"
    local_config.write_text("local settings", encoding="utf-8")
    explicit_config = machine_dir / "explicit.conf"
    explicit_config.write_text("explicit settings", encoding="utf-8")
    monkeypatch.setattr(machine_env, "PLATFORM", Platform.MACOS)

    manifest = load_machine("test", env=selected_env)

    assert len(manifest.files) == 1
    override = manifest.files[0]
    assert override.source == str(explicit_config if explicit else local_config)
    assert override.target == str(Path(selected_env["HOME"]) / ".example/config")
    assert override.mode == 0o600
    assert override.platforms == [Platform.UNIX, Platform.WINDOWS]
    filtered = load_machine("test", ["example"], env=selected_env)
    assert filtered.files == manifest.files
    assert filtered.pkg_managers == [PkgManager.BREW]


def test_only_declared_modules_are_included(monkeypatch, tmp_path: Path, selected_env) -> None:
    monkeypatch.setattr(machine_env, "ROOT", tmp_path)
    monkeypatch.setattr(machine_env, "PLATFORM", Platform.WINDOWS)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "core").mkdir()
    (config_dir / "core" / "module.py").write_text(
        "from app.models import Module\nmodule = Module()\n"
    )
    (config_dir / "apps").mkdir()
    (config_dir / "apps" / "module.py").write_text(
        "from app.models import Module\nmodule = Module()\n"
    )
    machines_dir = tmp_path / "machines"
    machines_dir.mkdir()
    (machines_dir / "empty").mkdir()
    (machines_dir / "empty" / "machine.py").write_text(
        """
from app.models import Machine
manifest = Machine(modules=['apps'])
"""
    )
    (machines_dir / "declared").mkdir()
    (machines_dir / "declared" / "machine.py").write_text(
        "from app.models import Machine, Package, PkgManager\n"
        "manifest = Machine(pkg_managers=[PkgManager.WINGET], "
        "packages=[Package(winget='Example.App')])\n"
    )
    assert load_machine("empty", env=selected_env).modules == ["apps"]
    assert load_machine("declared", env=selected_env).modules == []


def test_platform_matching_is_directional_and_shared(monkeypatch, tmp_path: Path) -> None:
    expected = {
        Platform.MACOS: {Platform.MACOS, Platform.UNIX},
        Platform.LINUX: {Platform.LINUX, Platform.UNIX},
        Platform.WSL: {Platform.WSL, Platform.LINUX, Platform.UNIX},
        Platform.WINDOWS: {Platform.WINDOWS},
        Platform.UNIX: {Platform.UNIX},
    }
    for platform, matches in expected.items():
        monkeypatch.setattr(machine_env, "PLATFORM", platform)
        for target in Platform:
            assert platform.is_a(target) == (target in matches)
            file = FileMapping(source="source", target="target", platforms=[target])
            package = Package(name="example", brew="example", platforms=[target])
            assert file.applies_to(platform) == (target in matches)
            assert package.applies_to(platform) == (target in matches)
            tag = "win" if target == Platform.WINDOWS else target.value
            script = tmp_path / f"setup.{tag}.sh"
            script.write_text("#!/bin/sh\n")
            assert bool(machine_loader._resolve_scripts([str(script)])) == (target in matches)
        assert FileMapping(source="source", target="target").applies_to(platform)
        assert not FileMapping(source="source", target="target", platforms=[]).applies_to(platform)
        script = tmp_path / "setup.sh"
        script.write_text("#!/bin/sh\n")
        assert machine_loader._resolve_scripts([str(script)]) == [str(script)]


@pytest.mark.parametrize("selection", ["tools.editor", "tools"])
def test_nested_modules_discovery_and_resolution(
    monkeypatch, tmp_path: Path, selection: str, selected_env
) -> None:
    monkeypatch.setattr(machine_env, "ROOT", tmp_path)
    config = tmp_path / "config"
    for name in ["core", "tools/base", "tools/editor", "toolsmith/editor", "tools/editor/assets"]:
        directory = config / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "module.py").write_text("from app.models import Module\nmodule = Module()\n")
    editor = config / "tools" / "editor"
    (editor / "module.py").write_text(
        "from app.models import Module, FileMapping\n"
        "module = Module(depends=['tools.base'], "
        "files=[FileMapping(source='settings.json', target='~/.editor.json')])\n"
    )
    (editor / "settings.json").write_text("{}\n")
    (editor / "scripts").mkdir()
    script = editor / "scripts" / "init_editor.unix.sh"
    script.write_text("#!/bin/sh\n")
    machines = tmp_path / "machines"
    machines.mkdir()
    (machines / "test").mkdir()
    (machines / "test" / "machine.py").write_text(
        f"""
from app.models import Machine
manifest = Machine(modules=[{selection!r}])
"""
    )

    assert list_modules() == ["core", "tools.base", "tools.editor", "toolsmith.editor"]
    manifest = load_machine("test", env=selected_env)
    assert manifest.modules == ["tools.base", "tools.editor"]
    assert manifest.files[0].source == str(editor / "settings.json")
    assert manifest.scripts == [str(script)]

    filtered = load_machine("test", ["tools.editor"], env=selected_env)
    assert filtered.modules == ["tools.base", "tools.editor"]
    assert filtered.files == manifest.files
    assert filtered.scripts == manifest.scripts


@pytest.mark.parametrize(
    "package,managers,error",
    [
        ("Package()", "[]", "no install source"),
        ("Package(cmd='setup')", "[]", "require a name"),
        ("Package(brew='example')", "[]", "manager not declared"),
        ("Package(snap='example --classic')", "[PkgManager.SNAP]", "must be a package ID"),
    ],
)
def test_loader_rejects_invalid_package_declarations(
    monkeypatch, tmp_path, selected_env, package, managers, error
):
    monkeypatch.setattr(machine_env, "ROOT", tmp_path)
    monkeypatch.setattr(machine_env, "PLATFORM", Platform.LINUX)
    directory = tmp_path / "machines" / "test"
    directory.mkdir(parents=True)
    (directory / "machine.py").write_text(
        "from app.models import Machine, Package, PkgManager\n"
        f"manifest = Machine(pkg_managers={managers}, packages=[{package}])\n"
    )

    with pytest.raises(ValueError, match=error):
        load_machine("test", env=selected_env)


def test_package_source_is_not_a_declaration_field():
    assert "selected_source" not in signature(Package).parameters
    assert "selected_source" not in Package.model_json_schema()["properties"]
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        Package.model_validate({"brew": "example", "selected_source": "brew"})


def test_loader_resolves_package_sources_without_querying_installed_tools(
    monkeypatch, tmp_path, selected_env
):
    monkeypatch.setattr(machine_env, "ROOT", tmp_path)
    monkeypatch.setattr(machine_env, "PLATFORM", Platform.WSL)
    directory = tmp_path / "machines" / "test"
    directory.mkdir(parents=True)
    (directory / "machine.py").write_text(
        "from app.models import Machine, Package, PkgManager\n"
        "manifest = Machine(pkg_managers=[PkgManager.SNAP, PkgManager.APT], packages=[\n"
        "    Package(apt='example', snap='example'),\n"
        "    Package(snap='classic-example', snap_classic=True),\n"
        "    Package(name='custom', cmd='setup', up_cmd=True),\n"
        "    Package(winget='Windows.Example'),\n"
        "])\n"
    )
    monkeypatch.setattr(
        machine_env.shutil, "which", lambda *args: pytest.fail("loader queried installed tools")
    )

    packages = load_machine("test", env=selected_env).packages

    assert [package.name for package in packages] == ["example", "classic-example", "custom"]
    assert [package.selected_source for package in packages] == ["apt", "snap", None]
    assert packages[1].snap == "classic-example"
    assert packages[1].snap_classic
