"""Explicit configuration and read-only host checks."""

from pathlib import Path

from app import env
from app.models import Configuration, Package, PkgManager, Platform
from app.shell import find_executable


def validate_full_disk_access() -> None:
    """Probe macOS protected-file access without reading the file's contents."""
    if not env.is_macos:
        return

    # The user's privacy database is FDA-protected; absence is inconclusive.
    path = Path.home() / "Library" / "Application Support" / "com.apple.TCC" / "TCC.db"
    try:
        with path.open("rb"):
            pass
    except FileNotFoundError:
        return
    except PermissionError:
        raise PermissionError(
            "Cannot open the macOS privacy database. Enable Full Disk Access for your "
            "terminal or editor in System Settings > Privacy & Security > Full Disk Access, "
            "then restart it and retry."
        ) from None


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
    if package.snap_classic and not package.snap:
        raise ValueError(f"Package '{name}': snap_classic requires a Snap source")

    for source, value in package.sources.items():
        if isinstance(value, str) and (
            not value or value.startswith("-") or any(character.isspace() for character in value)
        ):
            raise ValueError(f"Package '{name}': {source} must be a package ID")
        if isinstance(value, int) and value <= 0:
            raise ValueError(f"Package '{name}': {source} must be a positive ID")


def validate_configuration(configuration: Configuration, platform: Platform) -> None:
    """Check resolved inputs and manager declarations, not live manager readiness."""
    # Optional managers must be compatible even when no selected package uses them.
    for manager, supported in (
        (PkgManager.MAS, Platform.MAC),
        (PkgManager.SNAP, Platform.LINUX),
        (PkgManager.SCOOP, Platform.WIN),
    ):
        if manager in configuration.pkg_managers and not platform.is_a(supported):
            raise ValueError(f"{manager} is not supported on {platform}")

    # Source choice is fixed by resolution, never by executable availability.
    for package in configuration.packages:
        source = package.selected_source
        if source is None:
            if not package.name:
                raise ValueError("Command-backed packages require a name")
            continue
        manager = PkgManager.BREW if source == "cask" else PkgManager(source)
        if manager not in configuration.pkg_managers:
            raise ValueError(f"Package '{package.name}': manager not declared for {source}")

    # Only effective mappings and applicable scripts need to exist.
    for file in configuration.files:
        if not file.source.exists():
            raise ValueError(f"File source missing: {file.source}")
    for script in configuration.scripts:
        if not script.is_file():
            raise ValueError(f"Script missing: {script}")
