"""Machine manifest models and loaders."""

import importlib.util
from pathlib import Path
from typing import Self

from pydantic import BaseModel, model_validator

# MARK: Models


class FileMapping(BaseModel):
    """A config file or directory to symlink.

    Paths are relative to the owning module or machine directory.
    Resolved to absolute paths by the loader.
    """

    source: str
    target: str  # absolute or ~ path


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
    """A composable unit of configuration.

    Groups related files, packages, and scripts for a single concern
    (e.g. git, shell). Defined in ``config/<name>/module.py``.

    Scripts under a ``scripts/`` subdirectory are auto-discovered by
    the loader.  Explicit entries in ``scripts`` are still supported
    for files outside that directory (e.g. ``init_keys.py`` in the
    module root).
    """

    name: str = ""
    depends: list[str] = []  # modules that must be included before this one
    files: list[FileMapping] = []
    packages: list[Package] = []
    scripts: list[str] = []  # paths relative to module dir
    required_env: list[str] = []  # env vars a manifest must provide
    overrides: dict[str, str] = {}  # local override files: filename → target


class MachineManifest(BaseModel):
    """Complete machine declaration.

    Composes modules and adds machine-specific overrides.
    Defined in ``machines/<id>/manifest.py``.
    """

    name: str | None = None  # public display name; defaults to machine ID
    modules: list[str | Module] = []
    files: list[FileMapping] = []  # machine-specific file mappings
    packages: list[Package] = []  # machine-specific packages
    scripts: list[str] = []  # paths relative to machine dir
    env: dict[str, str] = {}


# MARK: Package Helpers


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


# MARK: Discovery


def list_modules(root: Path) -> list[str]:
    """List available module names by scanning ``config/``.

    Discovers both directory modules (``config/<name>/module.py``)
    and flat modules (``config/<name>.py``).
    """
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
    """List available machine IDs by scanning ``machines/``.

    Discovers both directory manifests (``machines/<id>/manifest.py``)
    and flat manifests (``machines/<id>.py``).
    """
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


# MARK: Loaders


def load_module(name: str, root: Path) -> Module:
    """Load a module from ``config/<name>/module.py`` or ``config/<name>.py``.

    Directory modules get file/script path resolution and auto-discovery
    of a ``scripts/`` subdirectory.  Flat modules (single ``.py`` file)
    are for packages-only definitions with no associated files.
    """
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

    # Flat modules have no directory — skip path resolution
    if not dir_path.exists():
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
            if script.is_file() and script.suffix in {".sh", ".py", ".ps1"}:
                spath = str(script)
                if spath not in existing:
                    result.scripts.append(spath)

    return result


def load_manifest(machine_id: str, root: Path) -> MachineManifest:
    """Load a machine manifest from ``machines/<id>/manifest.py`` or
    ``machines/<id>.py``.

    Directory manifests get file/script path resolution and
    auto-discovery.  Flat manifests (single ``.py`` file) are for
    lightweight definitions with no machine-specific files.
    """
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

    # Flat manifests have no directory — skip path/script resolution
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
    for mod_ref in result.modules:
        name = mod_ref if isinstance(mod_ref, str) else mod_ref.name
        mod_obj = load_module(name, root)
        for filename, target in mod_obj.overrides.items():
            local_file = machine_dir / filename
            if local_file.exists():
                already = any(f.target == target for f in result.files)
                if not already:
                    result.files.append(FileMapping(source=str(local_file), target=target))

    # Auto-discover scripts/ directory
    scripts_dir = machine_dir / "scripts"
    if scripts_dir.is_dir():
        existing = set(result.scripts)
        for script in sorted(scripts_dir.iterdir()):
            if script.is_file() and script.suffix in {".sh", ".py", ".ps1"}:
                path = str(script)
                if path not in existing:
                    result.scripts.append(path)

    return result


# MARK: Helpers


def _resolve_deps(modules: list[str | Module], root: Path) -> list[str | Module]:
    """Resolve module dependencies and auto-include ``pkgs``.

    Walks each module's ``depends`` list and inserts missing deps
    before the dependent.  If any resolved module declares packages,
    the ``pkgs`` module is auto-included at the front (if it
    exists and wasn't already listed).
    """
    resolved: list[str | Module] = []
    seen: set[str] = set()
    for mod_ref in modules:
        name = mod_ref if isinstance(mod_ref, str) else mod_ref.name
        mod_obj = load_module(name, root)
        for dep in mod_obj.depends:
            if dep not in seen:
                seen.add(dep)
                resolved.append(dep)
        if name not in seen:
            seen.add(name)
            resolved.append(mod_ref)

    # Auto-include 'pkgs' when any module declares packages
    if "pkgs" not in seen:
        has_pkgs = any(
            (load_module(m, root) if isinstance(m, str) else m).packages for m in resolved
        )
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
