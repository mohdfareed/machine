"""Manifest dependency and override behavior tests."""

import shutil
import sys
from inspect import signature
from pathlib import Path

import pytest
from app import env as machine_env
from app import machine as machine_loader
from app.discovery import list_machines, list_modules
from app.machine import load_machine
from app.models import FileMapping, Machine, Package, PkgManager, Platform
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
def selected_env(tmp_path: Path, monkeypatch) -> dict[str, str]:
    values = {
        "HOME": str(tmp_path / "home"),
        "USERPROFILE": str(tmp_path / "home"),
        "APPDATA": str(tmp_path / "app-data"),
        "LOCALAPPDATA": str(tmp_path / "local-app-data"),
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    return values


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
            load_machine(machine_id, validate=True)


@pytest.mark.parametrize(
    "values,error",
    [
        ({"BAD;NAME": "value"}, "Invalid environment variable name"),
        ({"PUBLIC": "before\0after"}, "contains a null character"),
    ],
)
def test_loader_rejects_environment_unsafe_for_processes_or_shells(
    monkeypatch, tmp_path, values, error
):
    monkeypatch.setattr(machine_env, "ROOT", tmp_path)
    directory = tmp_path / "machines" / "test"
    directory.mkdir(parents=True)
    (directory / "machine.py").write_text(
        "from app.models import Machine\n" + f"manifest = Machine(env={values!r})\n"
    )

    with pytest.raises(ValueError, match=error):
        load_machine("test")


@pytest.mark.parametrize(
    "platform,expected,sources",
    [
        (Platform.MAC, [PkgManager.BREW, PkgManager.MAS], ["cask", "brew", "mas"]),
        (Platform.WIN, [PkgManager.WINGET, PkgManager.SCOOP], ["winget", "scoop", "scoop"]),
        (Platform.WSL, [PkgManager.BREW], ["brew", "brew"]),
    ],
)
def test_fixed_platform_managers_and_source_order(
    monkeypatch, tmp_path, selected_env, platform, expected, sources
):
    monkeypatch.setattr(machine_env, "ROOT", tmp_path)
    monkeypatch.setattr(machine_env, "PLATFORM", platform)
    monkeypatch.setattr(
        shutil, "which", lambda *args: pytest.fail("loader queried installed tools")
    )
    directory = tmp_path / "machines" / "test"
    directory.mkdir(parents=True)
    (directory / "machine.py").write_text(
        "from app.models import Machine, Package\n"
        "manifest = Machine(packages=[\n"
        "    Package(brew='example', cask='example', mas=123, winget='Example.App', "
        "scoop='example', cmd='setup'),\n"
        "    Package(brew='example', mas=123, scoop='example'),\n"
        "    Package(mas=123, scoop='example'),\n"
        "])\n"
    )

    configuration = load_machine("test", validate=True)
    assert configuration.pkg_managers == expected
    assert [package.selected_source for package in configuration.packages] == sources

    (directory / "machine.py").write_text("from app.models import Machine\nmanifest = Machine()\n")
    assert load_machine("test", validate=True).pkg_managers == expected


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
        "    FileMapping(source=Path('settings.conf'), target='~/$HOME/${HOME}/%HOME%'),\n"
        "    FileMapping(source='missing.conf', target='$UNDEFINED/config', "
        "platforms=[Platform.WIN]),\n"
        "])\n"
    )
    (selected / "scripts").mkdir()
    (selected / "scripts" / "setup.win.ps1").write_text("")
    (selected / "scripts" / "_helper.py").write_text("")
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
        "manifest = Machine(modules=[selected, other], "
        f"env={{'HOME': {str(tmp_path / 'selected-home')!r}, "
        f"'USERPROFILE': {str(tmp_path / 'selected-home')!r}}})\n"
    )
    (machine / "scripts").mkdir()
    (machine / "scripts" / "setup.unix.sh").write_text("#!/bin/sh\n")

    configuration = load_machine("test", ["selected"], validate=True)
    assert [file.source for file in configuration.files] == [source]
    assert configuration.files[0].target == (
        Path(selected_env["HOME"]) / "$HOME" / "${HOME}" / "%HOME%"
    )
    assert configuration.scripts == []

    source.unlink()
    assert [file.source for file in load_machine("test", ["selected"]).files] == [source]
    with pytest.raises(ValueError, match="File source missing"):
        load_machine("test", ["selected"], validate=True)


@pytest.mark.parametrize(
    "target", ["relative/config", "$DEV/config", "${DEV}/config", "%DEV%/config"]
)
def test_loader_rejects_nonabsolute_targets(monkeypatch, tmp_path, target):
    monkeypatch.setattr(machine_env, "ROOT", tmp_path)
    monkeypatch.setenv("DEV", str(tmp_path))
    directory = tmp_path / "machines" / "test"
    directory.mkdir(parents=True)
    (directory / "machine.py").write_text(
        "from app.models import Machine, FileMapping\n"
        f"manifest = Machine(env={{'DEV': {str(tmp_path)!r}}}, "
        f"files=[FileMapping(source='config', target={target!r})])\n"
    )

    with pytest.raises(ValueError, match="must be absolute"):
        load_machine("test")


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
            load_machine("test")
    else:
        manifest = load_machine("test")
        assert manifest.modules == ["base.common", "base.network", "client", "server"]
        assert load_machine("test", ["server"]).modules == manifest.modules

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
        "module = Module(files=[FileMapping(source='missing', target='~/.example/config')],\n"
        "overrides=[FileMapping(\n"
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

    manifest = load_machine("test")

    assert len(manifest.files) == 1
    override = manifest.files[0]
    assert override.source == (explicit_config if explicit else local_config)
    assert override.target == Path(selected_env["HOME"]) / ".example/config"
    assert override.mode == 0o600
    assert override.platforms == [Platform.UNIX, Platform.WIN]
    filtered = load_machine("test", ["example"])
    assert len(filtered.files) == 1
    assert filtered.files[0].source == local_config
    assert filtered.files[0].target == override.target
    assert filtered.files[0].mode == override.mode
    assert filtered.files[0].platforms == override.platforms
    assert filtered.pkg_managers == [PkgManager.BREW, PkgManager.MAS]


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
    assert load_machine("empty").modules == ["apps"]
    assert load_machine("declared").modules == []


def test_platform_matching_is_directional_and_shared(monkeypatch, tmp_path: Path) -> None:
    expected = {
        Platform.MAC: {Platform.MAC, Platform.UNIX},
        Platform.WSL: {Platform.WSL, Platform.UNIX},
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
            script = tmp_path / f"setup.{tag}.py"
            script.write_text("pass\n")
            assert bool(machine_loader._resolve_scripts([script])) == (target in matches)
        assert FileMapping(source=Path("source"), target=Path("target")).applies_to(platform)
        assert not FileMapping(
            source=Path("source"), target=Path("target"), platforms=[]
        ).applies_to(platform)
        script = tmp_path / "setup.py"
        script.write_text("pass\n")
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

    (machines / "test" / "scripts").mkdir()
    machine_script = machines / "test" / "scripts" / "setup.unix.sh"
    machine_script.write_text("#!/bin/sh\n")

    assert list_modules() == [
        "core",
        "tools.base",
        "tools.editor",
        "tools.editor.assets",
        "toolsmith.editor",
    ]
    manifest = load_machine("test")
    assert manifest.modules == ["tools.base", "tools.editor", "tools.editor.assets"]
    assert manifest.files[0].source == editor / "settings.json"
    assert manifest.scripts == [script, machine_script]

    for module_filter in [["tools.editor"], ["tools"], ["tools", "tools.editor"]]:
        filtered = load_machine("test", module_filter)
        assert filtered.modules == manifest.modules
        assert filtered.files == manifest.files
        assert filtered.scripts == [script]

    for unknown in ["editor", "tool", "toolsmith"]:
        with pytest.raises(FileNotFoundError, match="No module or group"):
            load_machine("test", [unknown])


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

    configuration = load_machine("test")
    assert configuration.modules == ["work.editor", "home.editor"]
    assert [package.name for package in configuration.packages] == [
        "config.work.editor.module",
        "config.home.editor.module",
    ]
    for group in ["work", "home"]:
        filtered = load_machine("test", [group])
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
    for name, value in next_env.items():
        monkeypatch.setenv(name, value)
    reloaded = load_machine("test")
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
        ("config.plain", "No module or group"),
        ("xml.etree", "Expected a config module or group"),
    ],
)
def test_loader_rejects_unknown_references(monkeypatch, tmp_path, selected_env, reference, error):
    monkeypatch.setattr(machine_env, "ROOT", tmp_path)
    config = tmp_path / "config"
    config.mkdir()
    (config / "__init__.py").touch()
    (config / "plain.py").write_text("")
    machine = tmp_path / "machines" / "test"
    machine.mkdir(parents=True)
    (machine / "machine.py").write_text(
        "from app.models import Machine\n"
        f"import {reference}\n"
        f"manifest = Machine(modules=[{reference}])\n"
    )

    with pytest.raises((ValueError, FileNotFoundError), match=error):
        load_machine("test")


@pytest.mark.parametrize(
    "package,error",
    [
        ("Package()", "no install source"),
        ("Package(platforms=[])", "no install source"),
        ("Package(winget='', platforms=[Platform.WIN])", "must be a package ID"),
        ("Package(cmd='setup')", "require a name"),
        ("Package(brew='example', up_cmd=True)", "requires cmd"),
        ("Package(brew='--invalid')", "must be a package ID"),
        ("Package(mas=0)", "must be a positive ID"),
        ("Package(winget='Example.App', cmd='setup')", "require a name"),
    ],
)
def test_loader_rejects_invalid_package_declarations(
    monkeypatch, tmp_path, selected_env, package, error
):
    monkeypatch.setattr(machine_env, "ROOT", tmp_path)
    monkeypatch.setattr(machine_env, "PLATFORM", Platform.MAC)
    directory = tmp_path / "machines" / "test"
    directory.mkdir(parents=True)
    (directory / "machine.py").write_text(
        "from app.models import Machine, Package, Platform\n"
        f"manifest = Machine(packages=[{package}])\n"
    )

    load_machine("test")
    with pytest.raises(ValueError, match=error):
        load_machine("test", validate=True)


def test_machine_managers_are_not_a_declaration_field():
    assert "pkg_managers" not in signature(Machine).parameters

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        Machine.model_validate({"pkg_managers": []})


def test_package_source_is_not_a_declaration_field():
    assert "selected_source" not in signature(Package).parameters
    assert "selected_source" not in Package.model_json_schema()["properties"]
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        Package.model_validate({"brew": "example", "selected_source": "brew"})


@pytest.mark.parametrize("validate", [False, True])
def test_loader_resolves_package_sources_without_querying_installed_tools(
    monkeypatch, tmp_path, selected_env, validate
):
    monkeypatch.setattr(machine_env, "ROOT", tmp_path)
    monkeypatch.setattr(machine_env, "PLATFORM", Platform.WSL)
    directory = tmp_path / "machines" / "test"
    directory.mkdir(parents=True)
    (directory / "machine.py").write_text(
        "from app.models import Machine, Package\n"
        "manifest = Machine(packages=[\n"
        "    Package(brew='example', cask='example'),\n"
        "    Package(brew='brew-example'),\n"
        "    Package(name='custom', cmd='setup', up_cmd=True),\n"
        "    Package(winget='Windows.Example'),\n"
        "])\n"
    )
    monkeypatch.setattr(
        shutil, "which", lambda *args: pytest.fail("loader queried installed tools")
    )

    packages = load_machine("test", validate=validate).packages

    assert [package.name for package in packages] == ["example", "brew-example", "custom"]
    assert [package.selected_source for package in packages] == ["brew", "brew", None]
