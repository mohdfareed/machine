"""Load ready-to-use machine configuration."""

import importlib.util
from pathlib import Path
from types import ModuleType

from app import env as machine_env
from app.discovery import SCRIPT_SUFFIXES, list_modules, list_scripts
from app.models import (
    Configuration,
    FileMapping,
    Machine,
    Module,
    Package,
    PackageSource,
    PkgManager,
    Platform,
)

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Machine Configuration
# ═════════════════════════════════════════════════════════════════════════════


def load_machine(
    machine_id: str,
    module_names: list[str] | None = None,
    *,
    env: dict[str, str],
) -> Configuration:
    """Resolve selected declarations into validated inputs for the current platform."""
    # Load the machine declaration and resolve its local paths.
    machine_dir = machine_env.ROOT / "machines" / machine_id
    path = machine_dir / "machine.py"
    machine = getattr(_import_py(path), "manifest", None)
    if not isinstance(machine, Machine):
        raise TypeError(f"{path} must export 'manifest' as {Machine.__name__}")
    _resolve_paths(machine, machine_dir)

    # Load each module once, retaining prerequisites of selected modules.
    modules = _load_modules(machine.modules)
    if module_names:
        pending = _expand_modules(module_names, list(modules))
        selected = set(pending)
        while pending:
            dependencies = _reference_names(modules[pending.pop()].depends)
            for dependency in _expand_modules(dependencies, list(modules)):
                if dependency in selected:
                    continue
                selected.add(dependency)
                pending.append(dependency)
        modules = {name: module for name, module in modules.items() if name in selected}

    # Keep selected modules' overrides, with explicit machine mappings taking precedence.
    overrides: list[FileMapping] = []
    override_targets: set[Path] = set()
    for module in modules.values():
        for override in module.overrides:
            if not override.applies_to(machine_env.PLATFORM):
                continue
            override_targets.add(override.target)
            local_file = machine_dir / override.source
            if not local_file.exists():
                continue
            overrides.append(
                FileMapping(
                    source=local_file,
                    target=override.target,
                    mode=override.mode,
                    platforms=override.platforms,
                )
            )

    # Combine applicable inputs and validate them before any execution.
    managers = list(dict.fromkeys(machine.pkg_managers))
    _validate_managers(managers)
    files = [file for module in modules.values() for file in module.files] + overrides
    files.extend(
        file for file in machine.files if not module_names or file.target in override_targets
    )
    packages = [package for module in modules.values() for package in module.packages]
    scripts = [script for module in modules.values() for script in module.scripts]
    if not module_names:
        packages.extend(machine.packages)
        scripts.extend(machine.scripts)

    return Configuration(
        pkg_managers=managers,
        modules=list(modules),
        files=_resolve_files(files, env),
        packages=_resolve_packages(packages, managers),
        scripts=_resolve_scripts(scripts),
    )


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Module Resolution
# ═════════════════════════════════════════════════════════════════════════════


def _load_modules(selections: list[ModuleType]) -> dict[str, Module]:
    available = list_modules()
    resolved: dict[str, Module] = {}
    visiting: list[str] = []

    def _add(name: str) -> None:
        if name in resolved:
            return
        if name in visiting:
            raise ValueError(f"Circular module dependency: {' → '.join([*visiting, name])}")

        # Locate and load the module declaration.
        directory = machine_env.ROOT / "config" / Path(*name.split("."))
        path = directory / "module.py"
        module = getattr(_import_py(path), "module", None)
        if not isinstance(module, Module):
            raise TypeError(f"{path} must export 'module' as {Module.__name__}")
        _resolve_paths(module, directory)

        # Resolve prerequisites before recording this module.
        visiting.append(name)
        for dependency in _expand_modules(_reference_names(module.depends), available):
            _add(dependency)
        visiting.pop()
        resolved[name] = module

    # Expand selections before resolving their dependencies.
    for name in _expand_modules(_reference_names(selections), available):
        _add(name)

    return resolved


def _reference_names(references: list[ModuleType]) -> list[str]:
    names: list[str] = []
    for reference in references:
        # Accept imported config folders, not declaration files or unrelated Python modules.
        spec = reference.__spec__
        if (
            not reference.__name__.startswith("config.")
            or spec is None
            or spec.submodule_search_locations is None
        ):
            raise ValueError(f"Expected an imported config folder: {reference.__name__}")

        # Resolve against this checkout even when Python can see another config namespace.
        name = reference.__name__.removeprefix("config.")
        directory = (machine_env.ROOT / "config" / Path(*name.split("."))).resolve()
        if not any(
            Path(location).resolve() == directory for location in spec.submodule_search_locations
        ):
            raise ValueError(f"Config reference is outside this repository: {reference.__name__}")
        names.append(name)

    return names


def _expand_modules(selections: list[str], available: list[str]) -> list[str]:
    expanded: list[str] = []
    for selection in selections:
        parts = selection.split(".")
        if any(not part or any(char in part for char in "/\\:") for part in parts):
            raise ValueError(f"Invalid module name: {selection}")

        matches = [
            name for name in available if name == selection or name.startswith(selection + ".")
        ]

        if not matches:
            raise FileNotFoundError(f"No module or group: {selection}")
        expanded.extend(matches)

    return list(dict.fromkeys(expanded))


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Package Resolution
# ═════════════════════════════════════════════════════════════════════════════

_PLATFORM_SOURCES: dict[Platform, tuple[PackageSource, ...]] = {
    Platform.MAC: ("cask", "brew", "mas"),
    Platform.LINUX: ("apt", "snap", "brew"),
    Platform.WIN: ("winget", "scoop"),
}


def _validate_managers(managers: list[PkgManager]) -> None:
    supported = {
        PkgManager.BREW if source == "cask" else PkgManager(source)
        for platform, sources in _PLATFORM_SOURCES.items()
        if machine_env.PLATFORM.is_a(platform)
        for source in sources
    }
    for manager in managers:
        if manager not in supported:
            raise ValueError(f"{manager} is not supported on {machine_env.PLATFORM}")

    if PkgManager.MAS in managers and PkgManager.BREW not in managers:
        raise ValueError("mas requires brew in the machine's declared package managers")


def _resolve_packages(packages: list[Package], managers: list[PkgManager]) -> list[Package]:
    resolved: list[Package] = []
    preferred: list[PackageSource] = [
        source
        for platform, sources in _PLATFORM_SOURCES.items()
        if machine_env.PLATFORM.is_a(platform)
        for source in sources
    ]

    # Validate each package and select a source by platform preference.
    for package in packages:
        if not package.applies_to(machine_env.PLATFORM):
            continue  # Skip packages unsupported on the current platform.

        # Validate declaration rules explicitly, outside model construction.
        sources = package.sources
        name = package.name.strip() or (str(next(iter(sources.values()))) if sources else "")
        if not sources and not package.cmd:
            raise ValueError(f"Package '{name}' has no install source")
        if package.up_cmd is True and not package.cmd:
            raise ValueError(f"Package '{name}': up_cmd=True requires cmd")
        if package.snap_classic and not package.snap:
            raise ValueError(f"Package '{name}': snap_classic requires a Snap source")

        # Validate that each declared source is a non-empty string or positive integer.
        for source, value in sources.items():
            if isinstance(value, str) and (
                not value
                or value.startswith("-")
                or any(character.isspace() for character in value)
            ):
                raise ValueError(f"Package '{name}': {source} must be a package ID")
            if isinstance(value, int) and value <= 0:
                raise ValueError(f"Package '{name}': {source} must be a positive ID")

        # Select a declared source by platform preference, independently of installed tools.
        applicable: list[PackageSource] = [source for source in preferred if source in sources]
        package.selected_source = None
        if applicable:
            for source in applicable:
                manager = PkgManager.BREW if source == "cask" else PkgManager(source)
                if manager in managers:
                    package.selected_source = source
                    break

            # Require a declared manager for any applicable source.
            if package.selected_source is None:
                raise ValueError(
                    f"Package '{name}': manager not declared for " + ", ".join(applicable)
                )

        # Skip packages without a selected source or command.
        # This allows a module to declare a package without requiring a name.
        elif not package.cmd:
            continue

        # Infer manager-backed names in declaration order; custom commands need an explicit name.
        if package.selected_source is None and not package.name.strip():
            raise ValueError("Command-backed packages require a name")
        package.name = name
        resolved.append(package)

    return resolved


# ═════════════════════════════════════════════════════════════════════════════
# MARK: File and Script Resolution
# ═════════════════════════════════════════════════════════════════════════════


def _resolve_files(files: list[FileMapping], env: dict[str, str]) -> list[FileMapping]:
    # Later overrides replace earlier mappings before source validation.
    targets: dict[Path, FileMapping] = {}
    for file in files:
        if not file.applies_to(machine_env.PLATFORM):
            continue

        file.target = machine_env.resolve_path(file.target, env)
        targets[file.target] = file

    for file in targets.values():
        if not file.source.exists():
            raise ValueError(f"File source missing: {file.source}")
    return list(targets.values())


def _resolve_scripts(scripts: list[Path]) -> list[Path]:
    tags = {
        ".mac": Platform.MAC,
        ".linux": Platform.LINUX,
        ".unix": Platform.UNIX,
        ".win": Platform.WIN,
        ".wsl": Platform.WSL,
    }

    resolved: list[Path] = []
    for path in dict.fromkeys(scripts):
        if path.suffix.lower() not in SCRIPT_SUFFIXES or path.stem.startswith("_"):
            continue

        platforms = [tags[suffix.lower()] for suffix in path.suffixes if suffix.lower() in tags]
        if platforms and not any(machine_env.PLATFORM.is_a(platform) for platform in platforms):
            continue

        if not path.is_file():
            raise ValueError(f"Script missing: {path}")

        resolved.append(path)
    return resolved


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Declaration Helpers
# ═════════════════════════════════════════════════════════════════════════════


def _resolve_paths(config: Machine | Module, directory: Path) -> None:
    # Resolve explicit paths relative to the declaration directory.
    for file in config.files:
        file.source = directory / file.source
    config.scripts = [directory / script for script in config.scripts]

    # Discover additional scripts without repeating explicit entries.
    existing = set(config.scripts)
    config.scripts.extend(
        script for script in list_scripts(directory / "scripts") if script not in existing
    )


def _import_py(path: Path) -> ModuleType:
    if not path.is_file():
        raise FileNotFoundError(f"No declaration: {path}")

    name = ".".join(path.relative_to(machine_env.ROOT).with_suffix("").parts)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load: {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
