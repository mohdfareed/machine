#!/usr/bin/env python3
"""
Cross-platform package installer.
Reads JSON from CHEZMOI_PACKAGES and installs packages using
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

    for manager, pkgs in base.items():
        install_packages(manager, pkgs)
    for manager, pkgs in machine.items():
        install_packages(manager, pkgs)


def install_packages(manager: str, pkgs: list[Any]) -> None:
    pkg_manager = utils.PackageManager(manager)
    if not pkg_manager.is_supported():
        return
    if not pkg_manager.is_available():
        print(f"{manager} is not available, skipping...")
        return

    for pkg in pkgs:
        install_package(pkg_manager, pkg)


def install_package(pkg_manager: utils.PackageManager, pkg: Any) -> None:
    if isinstance(pkg, dict) and "script" in pkg:
        command = str(pkg["script"])  # type: ignore
        print(f"running script: {command}")
        utils.run(command)

    elif isinstance(pkg, str) or isinstance(pkg, int):
        print(f"{pkg_manager} installing {pkg}...")
        pkg_manager.install(str(pkg))

    else:
        print(f"invalid package format: {pkg}")


def load_packages(source: str) -> dict[str, list[Any]]:
    try:
        data = json.loads(os.environ.get("CHEZMOI_DATA", ""))
        return data.get(source, {})
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid CHEZMOI_DATA: {e}") from e


if __name__ == "__main__":
    try:  # run script
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as error:
        print(f"packages error: {error}", file=sys.stderr)
        sys.exit(1)
