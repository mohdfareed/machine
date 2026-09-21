"""Manifest dependency and override behavior tests."""

import sys
from inspect import signature
from pathlib import Path

import pytest
from app import env as machine_env
from app import machine as machine_loader
from app.discovery import list_machines, list_modules
from app.machine import load_machine
from app.models import FileMapping, Package, PkgManager, Platform
from pydantic import ValidationError


@pytest.fixture(autouse=True)
def isolate_config_imports(monkeypatch, tmp_path: Path):
    # Load each temporary catalog without retaining imported folders from another test.
    saved = {
        name: module
        for name, module in sys.modules.items()
        if name == "config" or name.startswith("config.")
    }
    for name in saved:
        del sys.modules[name]
    monkeypatch.syspath_prepend(str(tmp_path))
    yield
    for name in list(sys.modules):
        if name == "config" or name.startswith("config."):
            del sys.modules[name]
    sys.modules.update(saved)


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
        "pc": [Platform.WIN, Platform.WSL],
        "gleason": [Platform.WIN, Platform.WSL],
        "homelab": [Platform.MAC],
        "macbook": [Platform.MAC],
    }
    for machine_id in list_machines():
        for platform in platforms[machine_id]:
            monkeypatch.setattr(machine_env, "PLATFORM", platform)
            load_machine(machine_id, env=selected_env)


@pytest.mark.parametrize(
    "platform,additions,expected,source",
    [
        (Platform.MAC, "PkgManager.MAS, PkgManager.MAS", [PkgManager.BREW, PkgManager.MAS], "cask"),
        (Platform.WIN, "PkgManager.SCOOP", [PkgManager.WINGET, PkgManager.SCOOP], "winget"),
        (Platform.LINUX, "", [PkgManager.APT, PkgManager.BREW], "apt"),
        (
            Platform.WSL,
            "PkgManager.SNAP",
            [PkgManager.APT, PkgManager.BREW, PkgManager.SNAP],
            "apt",
        ),
    ],
)
def test_platform_managers_and_optional_additions(
    monkeypatch, tmp_path, selected_env, platform, additions, expected, source
):
    monkeypatch.setattr(machine_env, "ROOT", tmp_path)
    monkeypatch.setattr(machine_env, "PLATFORM", platform)
    monkeypatch.setattr(
        machine_env.shutil, "which", lambda *args: pytest.fail("loader queried installed tools")
    )
    directory = tmp_path / "machines" / "test"
    directory.mkdir(parents=True)
    (directory / "machine.py").write_text(
        "from app.models import Machine, Package, PkgManager\n"
        f"manifest = Machine(pkg_managers=[{additions}], packages=[\n"
        "    Package(brew='example', cask='example', apt='example', winget='Example.App'),\n"
        "])\n"
    )

    configuration = load_machine("test", env=selected_env)
    assert configuration.pkg_managers == expected
    assert configuration.packages[0].selected_source == source

    unsupported = PkgManager.MAS if platform == Platform.WIN else PkgManager.SCOOP
    (directory / "machine.py").write_text(
        "from app.models import Machine, PkgManager\n"
        f"manifest = Machine(pkg_managers=[PkgManager.{unsupported.name}])\n"
    )
    with pytest.raises(ValueError, match="is not supported"):
        load_machine("test", env=selected_env)


def test_load_machine_validates_only_applicable_selected_sources(
    monkeypatch, tmp_path: Path, selected_env
) -> None:
    monkeypatch.setattr(machine_env, "ROOT", tmp_path)
    monkeypatch.setattr(machine_env, "PLATFORM", Platform.MAC)
    selected = tmp_path / "config" / "selected"
    selected.mkdir(parents=True)
    (selected.parent / "__init__.py").touch()
    (selected / "module.py").write_text(
        "from pathlib import Path\n"
        "from app.models import FileMapping, Module, Platform\n"
        "module = Module(files=[\n"
        "    FileMapping(source=Path('settings.conf'), target='~/.config'),\n"
        "    FileMapping(source='missing.conf', target='$UNDEFINED/config', "
        "platforms=[Platform.WIN]),\n"
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
        "from config import selected, other\n"
        "manifest = Machine(modules=[selected, other], scripts=['missing.sh'])\n"
    )

    configuration = load_machine("test", ["selected"], env=selected_env)
    assert [file.source for file in configuration.files] == [source]
    assert configuration.files[0].target == Path(selected_env["HOME"]) / ".config"
    assert configuration.scripts == []

    source.unlink()
    with pytest.raises(ValueError, match="File source missing"):
        load_machine("test", ["selected"], env=selected_env)


@pytest.mark.parametrize("cycle", [False, True], ids=["dependencies", "dependency-cycle"])
def test_module_dependencies_loaded_once(monkeypatch, tmp_path: Path, cycle, selected_env) -> None:
    monkeypatch.setattr(machine_env, "ROOT", tmp_path)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "__init__.py").touch()
    machine_dir = tmp_path / "machines" / "test"
    machine_dir.mkdir(parents=True)
    for name, dependencies in {
        "core": [],
        "base/common": ["server"] if cycle else [],
        "base/network": [],
        "client": ["base"],
        "server": ["client"],
    }.items():
        (config_dir / name).mkdir(parents=True, exist_ok=True)
        (config_dir / name / "module.py").write_text(
            "from app.models import Module\n"
            + (f"from config import {', '.join(dependencies)}\n" if dependencies else "")
            + f"module = Module(depends=[{', '.join(dependencies)}])\n",
            encoding="utf-8",
        )
    (machine_dir / "machine.py").write_text(
        """
from app.models import Machine
from config import server, client
manifest = Machine(modules=[server, client])
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
        assert manifest.modules == ["base.common", "base.network", "client", "server"]
        assert load_machine("test", ["server"], env=selected_env).modules == manifest.modules

    expected = 4 if cycle else 5
    assert len(set(imported)) == expected
    assert len(imported) == expected * (1 if cycle else 2)


@pytest.mark.parametrize("explicit", [False, True], ids=["module-override", "explicit-mapping"])
def test_manifest_override_preserves_metadata(
    monkeypatch, tmp_path: Path, explicit, selected_env
) -> None:
    monkeypatch.setattr(machine_env, "ROOT", tmp_path)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "__init__.py").touch()
    (config_dir / "example").mkdir()
    (config_dir / "example" / "module.py").write_text(
        "from app.models import FileMapping, Module, Platform\n"
        "module = Module(overrides=[FileMapping(\n"
        "    source='local.conf', target='~/.example/config',\n"
        "    mode=0o600, platforms=[Platform.UNIX, Platform.WIN],\n"
        ")])\n",
        encoding="utf-8",
    )
    machine_dir = tmp_path / "machines" / "test"
    machine_dir.mkdir(parents=True)
    explicit_mapping = (
        "FileMapping(source='explicit.conf', target='~/.example/config', "
        "mode=0o600, platforms=[Platform.UNIX, Platform.WIN])"
        if explicit
        else ""
    )
    (machine_dir / "machine.py").write_text(
        "from app.models import FileMapping, Machine, Platform\n"
        "from config import example\n"
        "manifest = Machine(modules=[example], "
        f"files=[{explicit_mapping}])\n",
        encoding="utf-8",
    )
    local_config = machine_dir / "local.conf"
    local_config.write_text("local settings", encoding="utf-8")
    explicit_config = machine_dir / "explicit.conf"
    explicit_config.write_text("explicit settings", encoding="utf-8")
    monkeypatch.setattr(machine_env, "PLATFORM", Platform.MAC)

    manifest = load_machine("test", env=selected_env)

    assert len(manifest.files) == 1
    override = manifest.files[0]
    assert override.source == (explicit_config if explicit else local_config)
    assert override.target == Path(selected_env["HOME"]) / ".example/config"
    assert override.mode == 0o600
    assert override.platforms == [Platform.UNIX, Platform.WIN]
    filtered = load_machine("test", ["example"], env=selected_env)
    assert filtered.files == manifest.files
    assert filtered.pkg_managers == [PkgManager.BREW]


def test_only_declared_modules_are_included(monkeypatch, tmp_path: Path, selected_env) -> None:
    monkeypatch.setattr(machine_env, "ROOT", tmp_path)
    monkeypatch.setattr(machine_env, "PLATFORM", Platform.WIN)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "__init__.py").touch()
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
from config import apps
manifest = Machine(modules=[apps])
"""
    )
    (machines_dir / "declared").mkdir()
    (machines_dir / "declared" / "machine.py").write_text(
        "from app.models import Machine, Package\n"
        "manifest = Machine(packages=[Package(winget='Example.App')])\n"
    )
    assert load_machine("empty", env=selected_env).modules == ["apps"]
    assert load_machine("declared", env=selected_env).modules == []


def test_platform_matching_is_directional_and_shared(monkeypatch, tmp_path: Path) -> None:
    expected = {
        Platform.MAC: {Platform.MAC, Platform.UNIX},
        Platform.LINUX: {Platform.LINUX, Platform.UNIX},
        Platform.WSL: {Platform.WSL, Platform.LINUX, Platform.UNIX},
        Platform.WIN: {Platform.WIN},
        Platform.UNIX: {Platform.UNIX},
    }
    for platform, matches in expected.items():
        monkeypatch.setattr(machine_env, "PLATFORM", platform)
        for target in Platform:
            assert platform.is_a(target) == (target in matches)
            file = FileMapping(source=Path("source"), target=Path("target"), platforms=[target])
            package = Package(name="example", brew="example", platforms=[target])
            assert file.applies_to(platform) == (target in matches)
            assert package.applies_to(platform) == (target in matches)
            tag = {Platform.MAC: "mac", Platform.WIN: "win"}.get(target, target.value)
            script = tmp_path / f"setup.{tag}.sh"
            script.write_text("#!/bin/sh\n")
            assert bool(machine_loader._resolve_scripts([script])) == (target in matches)
        assert FileMapping(source=Path("source"), target=Path("target")).applies_to(platform)
        assert not FileMapping(
            source=Path("source"), target=Path("target"), platforms=[]
        ).applies_to(platform)
        script = tmp_path / "setup.sh"
        script.write_text("#!/bin/sh\n")
        assert machine_loader._resolve_scripts([script]) == [script]


@pytest.mark.parametrize("selection", ["tools.editor", "tools"])
def test_nested_modules_discovery_and_resolution(
    monkeypatch, tmp_path: Path, selection: str, selected_env
) -> None:
    monkeypatch.setattr(machine_env, "ROOT", tmp_path)
    monkeypatch.setattr(machine_env, "PLATFORM", Platform.MAC)
    config = tmp_path / "config"
    for name in ["core", "tools/base", "tools/editor", "toolsmith/editor", "tools/editor/assets"]:
        directory = config / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "module.py").write_text("from app.models import Module\nmodule = Module()\n")
    (config / "__init__.py").touch()
    editor = config / "tools" / "editor"
    (editor / "module.py").write_text(
        "from app.models import Module, FileMapping\n"
        "from config.tools import base\n"
        "module = Module(depends=[base], "
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
import config.{selection}
manifest = Machine(modules=[config.{selection}])
"""
    )

    assert list_modules() == ["core", "tools.base", "tools.editor", "toolsmith.editor"]
    manifest = load_machine("test", env=selected_env)
    assert manifest.modules == ["tools.base", "tools.editor"]
    assert manifest.files[0].source == editor / "settings.json"
    assert manifest.scripts == [script]

    for module_filter in [["tools.editor"], ["tools"], ["tools", "tools.editor"]]:
        filtered = load_machine("test", module_filter, env=selected_env)
        assert filtered.modules == ["tools.base", "tools.editor"]
        assert filtered.files == manifest.files
        assert filtered.scripts == manifest.scripts

    for unknown in ["editor", "tool", "toolsmith"]:
        with pytest.raises(FileNotFoundError, match="No module or group"):
            load_machine("test", [unknown], env=selected_env)


def test_same_leaf_modules_keep_distinct_inputs(monkeypatch, tmp_path, selected_env):
    monkeypatch.setattr(machine_env, "ROOT", tmp_path)
    monkeypatch.setattr(machine_env, "PLATFORM", Platform.MAC)
    machine = tmp_path / "machines" / "test"
    machine.mkdir(parents=True)
    (machine / "machine.py").write_text(
        "from app.models import Machine\n"
        "from config.work import editor as work_editor\n"
        "from config.home import editor as home_editor\n"
        "manifest = Machine(modules=[work_editor, home_editor])\n"
    )
    for group in ["work", "home"]:
        directory = tmp_path / "config" / group / "editor"
        directory.mkdir(parents=True)
        (directory / "module.py").write_text(
            "from app.models import FileMapping, Module, Package\n"
            "module = Module(files=[\n"
            f"    FileMapping(source='settings', target='~/{group}/settings')\n"
            "], overrides=[\n"
            f"    FileMapping(source='{group}.local', target='~/{group}/local')\n"
            "], packages=[Package(name=__name__, brew='editor', winget='Editor.App')])\n"
        )
        (directory / "settings").write_text(group)
        (machine / f"{group}.local").write_text(group)
    (tmp_path / "config" / "__init__.py").touch()

    configuration = load_machine("test", env=selected_env)
    assert configuration.modules == ["work.editor", "home.editor"]
    assert [package.name for package in configuration.packages] == [
        "config.work.editor.module",
        "config.home.editor.module",
    ]
    for group in ["work", "home"]:
        filtered = load_machine("test", [group], env=selected_env)
        assert filtered.modules == [f"{group}.editor"]
        assert [file.source for file in filtered.files] == [
            tmp_path / "config" / group / "editor" / "settings",
            machine / f"{group}.local",
        ]
        assert {file.target.parent for file in filtered.files} == {
            Path(selected_env["HOME"]) / group
        }

    # Cached folder imports must not reuse previously resolved paths or package sources.
    monkeypatch.setattr(machine_env, "PLATFORM", Platform.WIN)
    next_env = selected_env | {
        "HOME": str(tmp_path / "next-home"),
        "USERPROFILE": str(tmp_path / "next-home"),
    }
    reloaded = load_machine("test", env=next_env)
    assert [package.selected_source for package in reloaded.packages] == ["winget", "winget"]
    assert [package.selected_source for package in configuration.packages] == ["brew", "brew"]
    assert {file.target.parent for file in reloaded.files} == {
        Path(next_env["HOME"]) / group for group in ["work", "home"]
    }
    assert {file.target.parent for file in configuration.files} == {
        Path(selected_env["HOME"]) / group for group in ["work", "home"]
    }


@pytest.mark.parametrize(
    "reference,error",
    [
        ("config.plain", "Expected an imported config folder"),
        ("xml.etree", "Expected an imported config folder"),
        ("config.external", "outside this repository"),
    ],
)
def test_loader_rejects_references_outside_config_folders(
    monkeypatch, tmp_path, selected_env, reference, error
):
    monkeypatch.setattr(machine_env, "ROOT", tmp_path)
    config = tmp_path / "config"
    config.mkdir()
    (config / "__init__.py").touch()
    (config / "plain.py").write_text("")
    external = tmp_path / "external"
    (external / "config" / "external").mkdir(parents=True)
    if reference == "config.external":
        (external / "config" / "__init__.py").touch()
    monkeypatch.syspath_prepend(str(external))
    machine = tmp_path / "machines" / "test"
    machine.mkdir(parents=True)
    (machine / "machine.py").write_text(
        "from app.models import Machine\n"
        f"import {reference}\n"
        f"manifest = Machine(modules=[{reference}])\n"
    )

    with pytest.raises(ValueError, match=error):
        load_machine("test", env=selected_env)


def test_discovery_rejects_case_collisions(monkeypatch, tmp_path):
    monkeypatch.setattr(machine_env, "ROOT", tmp_path)
    config = tmp_path / "config"
    config.mkdir()
    # Simulate a case-sensitive host so this regression also runs on Windows and macOS.
    monkeypatch.setattr(Path, "walk", lambda path: iter([(path, ["Tools", "tools"], [])]))
    with pytest.raises(ValueError, match="differ only by case"):
        list_modules()


@pytest.mark.parametrize(
    "package,managers,error",
    [
        ("Package()", "[]", "no install source"),
        ("Package(cmd='setup')", "[]", "require a name"),
        ("Package(snap='example')", "[]", "manager not declared"),
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
        "manifest = Machine(pkg_managers=[PkgManager.SNAP], packages=[\n"
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
