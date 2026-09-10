"""Machine and module loading, resolution, and validation."""

import importlib.util
from pathlib import Path

from app.discovery import list_modules, list_scripts
from app.models import FileMapping, Machine, Module

# =============================================================================
# MARK: Validation
# =============================================================================


def validate_modules(modules: list[Module]) -> list[str]:
    """Return errors for missing file sources and scripts in resolved modules."""
    errors: list[str] = []

    for mod in modules:
        for fm in mod.files:
            if not Path(fm.source).exists():
                errors.append(f"Module '{mod.name}' file source missing: {fm.source}")
        for script in mod.scripts:
            if not Path(script).exists():
                errors.append(f"Module '{mod.name}' script missing: {script}")

    return errors


# =============================================================================
# MARK: Loaders
# =============================================================================


def load_module(name: str, root: Path) -> Module:
    """Load a dotted module name from its configuration directory."""
    # Locate the module declaration.
    parts = name.split(".")
    if any(not part or any(char in part for char in "/\\:") for part in parts):
        raise ValueError(f"Invalid module name: {name}")
    module_dir = root / "config" / Path(*parts)
    path = module_dir / "module.py"
    if not path.exists():
        raise FileNotFoundError(f"No module: {path}")

    # Load and validate the exported module.
    mod = _import_py(path, f"config.{name}.module")
    result = getattr(mod, "module", None)
    if result is None:
        raise AttributeError(f"Missing 'module' in {path}")
    if not isinstance(result, Module):
        raise TypeError(f"'module' must be {Module.__name__}, got {type(result)}")

    result.name = name

    # Resolve source paths relative to the module directory.
    for f in result.files:
        f.source = str(module_dir / f.source)
    for i, s in enumerate(result.scripts):
        result.scripts[i] = str(module_dir / s)

    # Discover additional scripts in the module directory.
    existing = set(result.scripts)
    result.scripts.extend(s for s in list_scripts(module_dir / "scripts") if s not in existing)

    return result


def load_manifest(machine_id: str, root: Path) -> Machine:
    """Load a machine manifest from ``machines/<id>/manifest.py``."""
    # Locate the machine declaration.
    machine_dir = root / "machines" / machine_id
    path = machine_dir / "manifest.py"
    if not path.exists():
        raise FileNotFoundError(f"No manifest: {path}")

    # Load and validate the exported machine.
    mod = _import_py(path, f"machines.{machine_id}.manifest")
    result = getattr(mod, "manifest", None)
    if result is None:
        raise AttributeError(f"Missing 'manifest' in {path}")
    if not isinstance(result, Machine):
        raise TypeError(f"'manifest' must be {Machine.__name__}, got {type(result)}")

    # Include core as the shared baseline for every machine.
    result.modules = ["core", *(name for name in result.modules if name != "core")]

    # Resolve source paths relative to the machine directory.
    for f in result.files:
        f.source = str(machine_dir / f.source)
    for i, s in enumerate(result.scripts):
        result.scripts[i] = str(machine_dir / s)

    # Include dependencies before their dependent modules.
    result.modules = _resolve_deps(result.modules, root)

    # Discover local overrides without replacing explicit machine mappings.
    for mod_name in result.modules:
        mod_obj = load_module(mod_name, root)
        for override in mod_obj.overrides:
            local_file = machine_dir / override.source
            if not local_file.exists():
                continue
            if any(f.target == override.target for f in result.files):
                continue

            result.files.append(
                FileMapping(
                    source=str(local_file),
                    target=override.target,
                    mode=override.mode,
                    platforms=override.platforms,
                )
            )

    # Discover additional scripts in the machine directory.
    existing = set(result.scripts)
    result.scripts.extend(s for s in list_scripts(machine_dir / "scripts") if s not in existing)

    return result


def resolve_modules(modules: list[str], root: Path) -> list[Module]:
    """Load full Module objects from module name strings."""
    return [load_module(name, root) for name in modules]


# =============================================================================
# MARK: Loading Helpers
# =============================================================================


def _resolve_deps(modules: list[str], root: Path) -> list[str]:

    resolved: list[str] = []
    seen: set[str] = set()

    def _add(name: str) -> None:
        if name in seen:
            return
        mod_obj = load_module(name, root)
        for dep in mod_obj.depends:
            _add(dep)
        seen.add(name)
        resolved.append(name)

    # Expand manifest groups before resolving dependencies.
    available = list_modules(root)
    for selection in modules:
        matches = [n for n in available if n == selection or n.startswith(selection + ".")]
        if not matches:
            raise FileNotFoundError(f"No module or group: {selection}")
        for name in matches:
            _add(name)

    return resolved


def _import_py(path: Path, module_name: str) -> object:

    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
