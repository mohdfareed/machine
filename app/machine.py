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
from app.validation import validate_configuration, validate_package

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Machine Configuration
# ═════════════════════════════════════════════════════════════════════════════


def load_machine(
    machine_id: str,
    module_names: list[str] | None = None,
    *,
    validate: bool = False,
) -> Configuration:
    """Resolve native-platform inputs, optionally checking declarations and sources."""
    # Load the machine declaration and resolve its local paths.
    machine_dir = machine_env.ROOT / "machines" / machine_id
    path = machine_dir / "machine.py"
    machine = getattr(_import_py(path), "manifest", None)
    if not isinstance(machine, Machine):
        raise TypeError(f"{path} must export 'manifest' as {Machine.__name__}")
    env = machine_env.build_env(machine_id, machine.env)
    for file in machine.files:
        file.source = machine_dir / file.source

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

    # Keep conventional overrides for the selected modules.
    overrides: list[FileMapping] = []

    for module in modules.values():
        for override in module.overrides:
            if not override.applies_to(machine_env.PLATFORM):
                continue

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

    # Combine applicable inputs and optionally validate the resolved configuration.

    files = [file for module in modules.values() for file in module.files] + overrides
    packages = [package for module in modules.values() for package in module.packages]
    scripts = [
        script
        for name in modules
        for script in list_scripts(machine_env.ROOT / "config" / Path(*name.split(".")) / "scripts")
    ]
    if not module_names:
        files.extend(machine.files)
        packages.extend(machine.packages)
        scripts.extend(list_scripts(machine_dir / "scripts"))

    configuration = Configuration(
        env=env,
        pkg_managers=list(_PLATFORM_MANAGERS[machine_env.PLATFORM]),
        modules=list(modules),
        files=_resolve_files(files),
        packages=_resolve_packages(packages, validate=validate),
        scripts=_resolve_scripts(scripts),
    )
    if validate:
        validate_configuration(configuration)
    return configuration


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
            raise ValueError(f"Circular module dependency: {' -> '.join([*visiting, name])}")

        # Locate and load the module declaration.
        directory = machine_env.ROOT / "config" / Path(*name.split("."))
        path = directory / "module.py"
        module = getattr(_import_py(path), "module", None)
        if not isinstance(module, Module):
            raise TypeError(f"{path} must export 'module' as {Module.__name__}")
        for file in module.files:
            file.source = directory / file.source

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
        if not reference.__name__.startswith("config."):
            raise ValueError(f"Expected a config module or group: {reference.__name__}")
        names.append(reference.__name__.removeprefix("config."))

    return names


def _expand_modules(selections: list[str], available: list[str]) -> list[str]:
    expanded: list[str] = []
    for selection in selections:
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

_PLATFORM_MANAGERS: dict[Platform, tuple[PkgManager, ...]] = {
    Platform.MAC: (PkgManager.BREW, PkgManager.MAS),
    Platform.WIN: (PkgManager.WINGET, PkgManager.SCOOP),
    Platform.WSL: (PkgManager.BREW,),
}

_PLATFORM_SOURCES: dict[Platform, tuple[PackageSource, ...]] = {
    Platform.MAC: ("cask", "brew", "mas"),
    Platform.WSL: ("brew",),
    Platform.WIN: ("winget", "scoop"),
}


def _resolve_packages(packages: list[Package], *, validate: bool) -> list[Package]:
    resolved: list[Package] = []
    preferred = _PLATFORM_SOURCES[machine_env.PLATFORM]

    for package in packages:
        if validate:
            validate_package(package)
        if not package.applies_to(machine_env.PLATFORM):
            continue
        sources = package.sources
        applicable: list[PackageSource] = [source for source in preferred if source in sources]
        if not applicable and not package.cmd:
            continue

        package.selected_source = applicable[0] if applicable else None
        package.name = package.name.strip()
        if not package.name and package.selected_source is not None:
            package.name = str(next(iter(sources.values())))
        resolved.append(package)

    return resolved


# ═════════════════════════════════════════════════════════════════════════════
# MARK: File and Script Resolution
# ═════════════════════════════════════════════════════════════════════════════


def _resolve_files(files: list[FileMapping]) -> list[FileMapping]:
    # Later overrides replace earlier mappings before source validation.
    targets: dict[Path, FileMapping] = {}
    for file in files:
        if not file.applies_to(machine_env.PLATFORM):
            continue

        file.target = file.target.expanduser()
        if not file.target.is_absolute():
            raise ValueError(f"Configured path must be absolute: {file.target}")
        targets[file.target] = file

    return list(targets.values())


def _resolve_scripts(scripts: list[Path]) -> list[Path]:
    tags = {
        ".mac": Platform.MAC,
        ".unix": Platform.UNIX,
        ".win": Platform.WIN,
        ".wsl": Platform.WSL,
    }

    resolved: list[Path] = []
    for path in dict.fromkeys(scripts):
        if path.suffix.lower() not in SCRIPT_SUFFIXES or path.stem.startswith("_"):
            continue
        if path.suffix.lower() == ".sh" and machine_env.PLATFORM.is_a(Platform.WIN):
            continue

        platforms = [tags[suffix.lower()] for suffix in path.suffixes if suffix.lower() in tags]
        if platforms and not any(machine_env.PLATFORM.is_a(platform) for platform in platforms):
            continue

        resolved.append(path)
    return resolved


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Declaration Helpers
# ═════════════════════════════════════════════════════════════════════════════


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
