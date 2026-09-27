"""Explicit configuration and read-only host checks."""

from app.models import Configuration, Package, PkgManager
from app.shell import find_executable


def validate_managers(managers: list[PkgManager], *, env: dict[str, str]) -> None:
    """Require every supplied manager to be available in the selected environment."""
    for manager in managers:
        if not find_executable(manager, env=env):
            raise FileNotFoundError(f"{manager} must already be installed and available on PATH")


def validate_package(package: Package) -> None:
    """Check install declarations before platform source selection."""
    name = package.name or next(iter(package.sources.values()), "")
    if not package.sources and not package.cmd:
        raise ValueError(f"Package '{name}' has no install source")
    if package.up_cmd is True and not package.cmd:
        raise ValueError(f"Package '{name}': up_cmd=True requires cmd")

    for source, value in package.sources.items():
        if isinstance(value, str) and (
            not value or value.startswith("-") or any(character.isspace() for character in value)
        ):
            raise ValueError(f"Package '{name}': {source} must be a package ID")
        if isinstance(value, int) and value <= 0:
            raise ValueError(f"Package '{name}': {source} must be a positive ID")


def validate_configuration(configuration: Configuration) -> None:
    """Check resolved inputs, not live manager readiness."""
    for package in configuration.packages:
        if package.selected_source is None and not package.name:
            raise ValueError("Command-backed packages require a name")

    # Only effective mappings and applicable scripts need to exist.
    for file in configuration.files:
        if not file.source.exists():
            raise ValueError(f"File source missing: {file.source}")
    for script in configuration.scripts:
        if not script.is_file():
            raise ValueError(f"Script missing: {script}")
