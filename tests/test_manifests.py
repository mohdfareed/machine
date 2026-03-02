"""Manifest and module validation tests."""

from pathlib import Path

import pytest

from machine.app import validate
from machine.manifest import (
    Module,
    list_machines,
    list_modules,
    load_manifest,
    load_module,
    resolve_modules,
)

ROOT = Path(__file__).resolve().parents[1]


# MARK: Module Tests


@pytest.fixture(params=list_modules(ROOT), ids=list_modules(ROOT))
def module(request: pytest.FixtureRequest) -> Module:
    return load_module(request.param, ROOT)


def test_module_loads(module: Module) -> None:
    """Every module.py imports and produces a Module."""
    assert isinstance(module, Module)
    assert module.name


def test_module_files_exist(module: Module) -> None:
    """Every file source in a module points to a real path."""
    for fm in module.files:
        assert Path(fm.source).exists(), f"{module.name}: missing {fm.source}"


def test_module_scripts_exist(module: Module) -> None:
    """Every script in a module points to a real path."""
    for script in module.scripts:
        assert Path(script).exists(), f"{module.name}: missing {script}"


# MARK: Manifest Tests


@pytest.fixture(params=list_machines(ROOT), ids=list_machines(ROOT))
def machine_id(request: pytest.FixtureRequest) -> str:
    return request.param


def test_manifest_loads(machine_id: str) -> None:
    """Every manifest.py imports and produces a MachineManifest."""
    manifest = load_manifest(machine_id, ROOT)
    assert manifest is not None


def test_manifest_modules_exist(machine_id: str) -> None:
    """Every module name in a manifest refers to an existing module."""
    manifest = load_manifest(machine_id, ROOT)
    available = set(list_modules(ROOT))
    for m in manifest.modules:
        assert m in available, f"{machine_id}: unknown module '{m}'"


def test_manifest_files_exist(machine_id: str) -> None:
    """Every machine-specific file source exists."""
    manifest = load_manifest(machine_id, ROOT)
    for fm in manifest.files:
        assert Path(fm.source).exists(), f"{machine_id}: missing {fm.source}"


def test_manifest_scripts_exist(machine_id: str) -> None:
    """Every machine-specific script exists."""
    manifest = load_manifest(machine_id, ROOT)
    for script in manifest.scripts:
        assert Path(script).exists(), f"{machine_id}: missing {script}"


def test_manifest_env_satisfies_modules(machine_id: str) -> None:
    """All module files and scripts exist for this machine."""
    manifest = load_manifest(machine_id, ROOT)
    modules = [load_module(m, ROOT) for m in manifest.modules]
    errors = validate(modules, machine_id)
    assert not errors, "\n".join(errors)


def test_manifest_overrides_included(machine_id: str) -> None:
    """Every module override file present in the machine dir is in the manifest files."""
    machine_dir = ROOT / "machines" / machine_id
    if not machine_dir.is_dir():
        pytest.skip("flat manifest - no machine directory")

    manifest = load_manifest(machine_id, ROOT)
    modules = resolve_modules(manifest.modules, ROOT)
    targeted = {fm.target for fm in manifest.files}

    missing: list[str] = []
    for mod in modules:
        for override in mod.overrides:
            local_file = machine_dir / override.source
            if local_file.exists() and override.target not in targeted:
                missing.append(
                    f"  module '{mod.name}': '{override.source}' exists"
                    f" but target '{override.target}' not in manifest files"
                )

    assert not missing, f"{machine_id} has unincluded overrides:\n" + "\n".join(missing)


# MARK: Validation Edge Cases


def test_ssh_module_loads_key_provisioning() -> None:
    """The ssh module includes the key-provisioning script."""
    ssh = load_module("ssh", ROOT)
    script_names = [Path(s).name for s in ssh.scripts]
    assert "init_keys.py" in script_names


def test_module_dependencies_auto_included() -> None:
    """Modules with depends= auto-include their dependencies."""
    ssh_server = load_module("ssh-server", ROOT)
    dep_names = ssh_server.depends
    assert "ssh" in dep_names

    # Build a manifest with only ssh-server - ssh should be auto-included
    from machine.manifest import MachineManifest

    manifest = MachineManifest(modules=["ssh-server"])
    resolved: list[str] = []
    seen: set[str] = set()
    for mod_name in manifest.modules:
        mod = load_module(mod_name, ROOT)
        for dep in mod.depends:
            if dep not in seen:
                seen.add(dep)
                resolved.append(dep)
        if mod_name not in seen:
            seen.add(mod_name)
            resolved.append(mod_name)
    assert resolved == ["ssh", "ssh-server"]
