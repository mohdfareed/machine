"""Manifest and module validation tests.

Loads every module and every manifest, checks that:
- All modules import cleanly and produce valid Module objects
- All manifests import cleanly and produce valid MachineManifest objects
- All module file sources exist on disk
- All module/machine scripts exist on disk
- All required_env vars are satisfied by the manifest
- All referenced modules exist
"""

from pathlib import Path

import pytest

from machine.app import validate
from machine.manifest import (
    Module,
    list_machines,
    list_modules,
    load_manifest,
    load_module,
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
        name = m if isinstance(m, str) else m.name
        assert name in available, f"{machine_id}: unknown module '{name}'"


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
    """All required_env vars from included modules are provided."""
    manifest = load_manifest(machine_id, ROOT)
    modules = [
        load_module(m, ROOT) if isinstance(m, str) else m for m in manifest.modules
    ]
    errors = validate(modules, manifest.env, machine_id)
    assert not errors, "\n".join(errors)


# MARK: Validation Edge Cases


def test_missing_required_env_detected() -> None:
    """validate() catches modules whose required_env is not satisfied."""
    mod = Module(name="fake", required_env=["MISSING_VAR"])
    errors = validate([mod], {}, "test-machine")
    assert len(errors) == 1
    assert "MISSING_VAR" in errors[0]


def test_ssh_module_loads_key_provisioning() -> None:
    """The ssh module includes the key-provisioning script."""
    ssh = load_module("ssh", ROOT)
    script_names = [Path(s).name for s in ssh.scripts]
    assert "init_keys.py" in script_names


def test_module_dependencies_auto_included() -> None:
    """Modules with depends= auto-include their dependencies."""
    tunnel = load_module("vscode-tunnel", ROOT)
    assert "vscode" in tunnel.depends

    # Build a manifest with only vscode-tunnel — vscode should be auto-included
    from machine.manifest import MachineManifest

    manifest = MachineManifest(modules=["vscode-tunnel"])
    # Simulate load_manifest dependency resolution
    resolved: list[str] = []
    seen: set[str] = set()
    for name in manifest.modules:
        assert isinstance(name, str)
        mod = load_module(name, ROOT)
        for dep in mod.depends:
            if dep not in seen:
                seen.add(dep)
                resolved.append(dep)
        if name not in seen:
            seen.add(name)
            resolved.append(name)
    assert resolved == ["vscode", "vscode-tunnel"]
