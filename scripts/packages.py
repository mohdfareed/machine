#!/usr/bin/env python3
"""
Cross-platform package installer.
Reads JSON from CHEZMOI_DATA and installs packages using
the specified package managers.

Expected JSON structure:
{
    "base": {
        "manager": [
            "pkg",
            {"script": "command to run"},
        ],
    },
    "machine": {
        "manager": ["pkg"],
    }
}
"""

import json
import os
import sys
from typing import Any

import utils


def main() -> None:
    base = load_packages("base")
    machine = load_packages("machine")

    base = filter_packages(base)
    machine = filter_packages(machine)

    if os.environ.get("DEBUG"):
        print(f"base packages: {json.dumps(base, indent=2)}")
        print(f"machine packages: {json.dumps(machine, indent=2)}")

    process_packages(base)
    process_packages(machine)


def load_packages(source: str) -> dict[str, list[Any]]:
    try:
        data = json.loads(os.environ.get("CHEZMOI_DATA", ""))
        return data.get(source, {})
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid CHEZMOI_DATA: {e}") from e


def filter_packages(
    packages: dict[str, list[Any]],
) -> dict[utils.PackageManager, list[Any]]:
    filtered = {}
    for manager, _ in packages.items():
        pkg_manager = utils.PackageManager(manager)
        if pkg_manager.is_supported():
            continue

        print(f"skipping unsupported package manager: {manager}")
        filtered[pkg_manager] = packages[manager]
    return filtered


def process_packages(
    packages: dict[utils.PackageManager, list[Any]],
) -> None:
    for manager, pkgs in packages.items():
        for pkg in pkgs:
            install_package(manager, pkg)


def install_package(pkg_manager: utils.PackageManager, pkg: Any) -> None:
    if isinstance(pkg, dict) and "script" in pkg:
        command = str(pkg["script"])  # type: ignore
        print(f"running script: {command}")
        utils.run(command)

    elif isinstance(pkg, str) or isinstance(pkg, int):
        if not pkg_manager.is_available():
            return
        print(f"{pkg_manager} installing {pkg}...")
        pkg_manager.install(str(pkg))


if __name__ == "__main__":
    try:  # run script
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as error:
        print(f"packages error: {error}", file=sys.stderr)
        sys.exit(1)
