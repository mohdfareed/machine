"""Cross-platform package installer."""

from __future__ import annotations

from typing import Any, Dict, List, Union

import yaml

from machine.core import (
    PackageManager,
    debug,
    error,
    get_machine_root,
    info,
    run,
)

# Type alias for package data structure
PackageData = Dict[str, List[Any]]
Package = Union[str, int, Dict[str, Any]]


def load_packages(machine_id: str) -> PackageData:
    """Load and merge packages from base config and machine config."""
    root = get_machine_root()
    base_path = root / "config" / "packages.yaml"
    machine_path = root / "machines" / machine_id / "packages.yaml"

    packages: PackageData = {}

    # Load base packages
    if base_path.exists():
        debug("packages", f"loading base packages: {base_path}")
        base_data: PackageData = yaml.safe_load(base_path.read_text()) or {}
        for manager, pkgs in base_data.items():
            packages[manager] = list(pkgs) if pkgs else []

    # Load and merge machine packages
    if machine_path.exists():
        debug("packages", f"loading machine packages: {machine_path}")
        machine_data: PackageData = (
            yaml.safe_load(machine_path.read_text()) or {}
        )
        for manager, pkgs in machine_data.items():
            pkg_list = list(pkgs) if pkgs else []
            if manager in packages:
                packages[manager].extend(pkg_list)
            else:
                packages[manager] = pkg_list

    return packages


def filter_packages(
    packages: PackageData,
) -> Dict[PackageManager, List[Any]]:
    """Filter packages to only supported package managers."""
    filtered: Dict[PackageManager, List[Any]] = {}

    for manager_name, pkgs in packages.items():
        try:
            manager = PackageManager(manager_name)
        except ValueError:
            error(f"unknown package manager: {manager_name}")
            continue

        if not manager.is_supported():
            debug("packages", f"skipping unsupported manager: {manager_name}")
            continue

        filtered[manager] = pkgs

    return filtered


def install_package(manager: PackageManager, package: Package) -> None:
    """Install a single package or run an inline script."""
    # Handle inline script
    if isinstance(package, dict) and "script" in package:
        command = str(package["script"])
        info(f"running: {command}")
        run(command, check=False)
        return

    # Handle regular package
    if not manager.is_available():
        debug("packages", f"{manager} not available, skipping: {package}")
        return

    package_name = str(package)
    info(f"{manager}: installing {package_name}")
    try:
        run(manager.install_command(package_name))
    except Exception as e:
        error(f"failed to install {package_name}: {e}")


def install_packages(machine_id: str) -> None:
    """Install all packages for a machine."""
    info(f"installing packages for machine: {machine_id}")

    packages = load_packages(machine_id)
    filtered = filter_packages(packages)

    for manager, pkgs in filtered.items():
        if not pkgs:
            continue
        info(f"processing {len(pkgs)} packages for {manager}")
        for pkg in pkgs:
            install_package(manager, pkg)
