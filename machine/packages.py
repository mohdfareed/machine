"""Cross-platform package installer."""

from __future__ import annotations

from typing import Any

import yaml

from machine.core import (
    PackageManager,
    debug,
    error,
    get_machine_root,
    info,
    run,
)


def load_packages(machine_id: str) -> dict[str, list[Any]]:
    """Load and merge packages from base config and machine config."""
    root = get_machine_root()
    base_path = root / "config" / "packages.yaml"
    machine_path = root / "machines" / machine_id / "packages.yaml"

    packages: dict[str, list[Any]] = {}

    # Load base packages
    if base_path.exists():
        debug("packages", f"loading base packages: {base_path}")
        base_data = yaml.safe_load(base_path.read_text()) or {}
        for manager, pkgs in base_data.items():
            packages[manager] = pkgs or []

    # Load and merge machine packages
    if machine_path.exists():
        debug("packages", f"loading machine packages: {machine_path}")
        machine_data = yaml.safe_load(machine_path.read_text()) or {}
        for manager, pkgs in machine_data.items():
            if manager in packages:
                packages[manager].extend(pkgs or [])
            else:
                packages[manager] = pkgs or []

    return packages


def filter_packages(
    packages: dict[str, list[Any]],
) -> dict[PackageManager, list[Any]]:
    """Filter packages to only supported package managers."""
    filtered: dict[PackageManager, list[Any]] = {}

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


def install_package(manager: PackageManager, package: Any) -> None:
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
