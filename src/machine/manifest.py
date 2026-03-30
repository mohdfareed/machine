"""Machine manifest models and loaders."""

import importlib.util
from pathlib import Path
from typing import Self

from pydantic import BaseModel, model_validator

SCRIPT_SUFFIXES = {".sh", ".py", ".ps1"}


# # MARK: Models


class FileMapping(BaseModel):
    """A config file or directory to symlink."""

    source: str
    target: str


class Package(BaseModel):
    """A package with per-manager install names."""

    name: str
    brew: str | None = None
    apt: str | None = None
    snap: str | None = None
    winget: str | None = None
    scoop: str | None = None
    mas: int | None = None
    script: str | None = None

    @model_validator(mode="after")
    def _check_source(self) -> Self:
        sources = [
            self.brew,
            self.apt,
            self.snap,
            self.winget,
            self.scoop,
            self.script,
        ]
        if self.mas is None and not any(s is not None for s in sources):
            raise ValueError(f"Package '{self.name}' has no install source")
        return self


class Module(BaseModel):
    """A composable unit of configuration."""

    name: str = ""
    depends: list[str] = []
    scripts: list[str] = []
    files: list[FileMapping] = []
    overrides: list[FileMapping] = []
    packages: list[Package] = []


class MachineManifest(BaseModel):
    """Complete machine declaration."""

    modules: list[str] = []
    scripts: list[str] = []
    files: list[FileMapping] = []
    packages: list[Package] = []


# # MARK: Package Helpers


def brew(*names: str) -> list[Package]:
    """Create brew packages. Include flags in the name: ``'pkg --flag'``."""
    return [Package(name=n.split()[0], brew=n) for n in names]


def cask(*names: str) -> list[Package]:
    """Create brew cask packages."""
    return [Package(name=n.split()[0], brew=f"{n} --cask") for n in names]


def apt(*names: str) -> list[Package]:
    """Create apt packages."""
    return [Package(name=n.split()[0], apt=n) for n in names]


def snap(*names: str) -> list[Package]:
    """Create snap packages."""
    return [Package(name=n.split()[0], snap=n) for n in names]


def winget(*names: str) -> list[Package]:
    """Create winget packages."""
    return [Package(name=n.split()[0], winget=n) for n in names]


def scoop(*names: str) -> list[Package]:
    """Create scoop packages."""
    return [Package(name=n.split()[0], scoop=n) for n in names]


def mas(**apps: int) -> list[Package]:
    """Create Mac App Store packages: ``name=app_id``."""
    return [Package(name=k, mas=v) for k, v in apps.items()]


# # MARK: Discovery


def list_modules(root: Path) -> list[str]:
    """List available module names by scanning ``config/``."""
    modules_dir = root / "config"
    if not modules_dir.exists():
        return []
    names: set[str] = set()
    for entry in modules_dir.iterdir():
        if entry.is_dir() and (entry / "module.py").exists():
            names.add(entry.name)
        elif entry.is_file() and entry.suffix == ".py":
            names.add(entry.stem)
    return sorted(names)


def list_machines(root: Path) -> list[str]:
    """List available machine IDs by scanning ``machines/``."""
    machines_dir = root / "machines"
    if not machines_dir.exists():
        return []
    names: set[str] = set()
    for entry in machines_dir.iterdir():
        if entry.is_dir() and (entry / "manifest.py").exists():
            names.add(entry.name)
        elif entry.is_file() and entry.suffix == ".py":
            names.add(entry.stem)
    return sorted(names)


# # MARK: Loaders

_module_cache: dict[str, Module] = {}


def load_module(name: str, root: Path) -> Module:
    """Load a module from ``config/<name>/module.py`` or ``config/<name>.py``."""
    module_dir = root / "config" / name
    dir_path = module_dir / "module.py"
    flat_path = root / "config" / f"{name}.py"

    if dir_path.exists():
        path = dir_path
    elif flat_path.exists():
        path = flat_path
    else:
        raise FileNotFoundError(f"No module: {dir_path} or {flat_path}")

    mod = _import_py(path, f"config.{name}.module")
    result = getattr(mod, "module", None)
    if result is None:
        raise AttributeError(f"Missing 'module' in {path}")
    if not isinstance(result, Module):
        raise TypeError(f"'module' must be Module, got {type(result)}")

    result.name = name

    # Flat modules have no directory - skip path resolution
    if not dir_path.exists():
        _module_cache[name] = result
        return result

    # Resolve source paths relative to module dir
    for f in result.files:
        f.source = str(module_dir / f.source)
    for i, s in enumerate(result.scripts):
        result.scripts[i] = str(module_dir / s)

    # Auto-discover scripts/ directory
    scripts_dir = module_dir / "scripts"
    if scripts_dir.is_dir():
        existing = set(result.scripts)
        for script in sorted(scripts_dir.iterdir()):
            if script.is_file() and script.suffix in SCRIPT_SUFFIXES:
                spath = str(script)
                if spath not in existing:
                    result.scripts.append(spath)

    _module_cache[name] = result
    return result


def load_manifest(machine_id: str, root: Path) -> MachineManifest:
    """Load a machine manifest from ``machines/<id>/manifest.py`` or ``machines/<id>.py``."""
    machine_dir = root / "machines" / machine_id
    dir_path = machine_dir / "manifest.py"
    flat_path = root / "machines" / f"{machine_id}.py"

    if dir_path.exists():
        path = dir_path
        is_dir_manifest = True
    elif flat_path.exists():
        path = flat_path
        is_dir_manifest = False
    else:
        raise FileNotFoundError(f"No manifest: {dir_path} or {flat_path}")

    mod = _import_py(path, f"machines.{machine_id}.manifest")
    result = getattr(mod, "manifest", None)
    if result is None:
        raise AttributeError(f"Missing 'manifest' in {path}")
    if not isinstance(result, MachineManifest):
        raise TypeError(f"'manifest' must be MachineManifest, got {type(result)}")

    # Flat manifests have no directory - skip path/script resolution
    if not is_dir_manifest:
        result.modules = _resolve_deps(result.modules, root)
        return result

    # Resolve machine-specific file sources relative to machine dir
    for f in result.files:
        f.source = str(machine_dir / f.source)
    for i, s in enumerate(result.scripts):
        result.scripts[i] = str(machine_dir / s)

    # Resolve module dependencies (auto-include missing, ordered before dependents)
    result.modules = _resolve_deps(result.modules, root)

    # Auto-discover local overrides declared by modules
    for mod_name in result.modules:
        mod_obj = load_module(mod_name, root)
        for override in mod_obj.overrides:
            local_file = machine_dir / override.source
            if local_file.exists():
                already = any(f.target == override.target for f in result.files)
                if not already:
                    result.files.append(FileMapping(source=str(local_file), target=override.target))

    # Auto-discover scripts/ directory
    scripts_dir = machine_dir / "scripts"
    if scripts_dir.is_dir():
        existing = set(result.scripts)
        for script in sorted(scripts_dir.iterdir()):
            if script.is_file() and script.suffix in SCRIPT_SUFFIXES:
                path = str(script)
                if path not in existing:
                    result.scripts.append(path)

    return result


# # MARK: Helpers


def _resolve_deps(modules: list[str], root: Path) -> list[str]:
    """Resolve module dependencies recursively and auto-include ``pkgs``."""
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

    for name in modules:
        _add(name)

    # Auto-include 'pkgs' when any module declares packages
    if "pkgs" not in seen:
        has_pkgs = any(load_module(m, root).packages for m in resolved)
        if has_pkgs:
            resolved.insert(0, "pkgs")

    return resolved


def _import_py(path: Path, module_name: str) -> object:
    """Dynamically import a Python file."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve_modules(modules: list[str], root: Path) -> list[Module]:
    """Load full Module objects from module name strings."""
    return [load_module(name, root) for name in modules]
