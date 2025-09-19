#!/usr/bin/env python3
"""
Cross-platform package installer.

Reads JSON from CHEZMOI_DATA and installs packages using the specified
package managers. If CHEZMOI_DATA is not set, falls back to loading from
YAML files in the machine config directories.
Respects DEBUG and DRY_RUN environment variables.

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
  },
}
"""

import argparse
import json
import os
from pathlib import Path
from typing import Any

import utils


def main() -> None:
    base = load_packages("base")
    machine = load_packages("machine")

    utils.debug("pkgs", f"base packages: {json.dumps(base, indent=2)}")
    utils.debug("pkgs", f"machine packages: {json.dumps(machine, indent=2)}")

    process_packages(filter_packages(base))
    process_packages(filter_packages(machine))


def load_packages(source: str) -> dict[str, list[Any]]:
    chezmoi_data = os.environ.get("CHEZMOI_DATA", "")
    if not chezmoi_data:
        return find_packages(source)

    try:
        data: dict[str, dict[str, list[str]]] = json.loads(chezmoi_data)
        return data.get(source, {})
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid CHEZMOI_DATA: {e}") from e


def find_packages(source: str) -> dict[str, list[Any]]:
    try:
        import yaml  # type: ignore
    except ImportError:
        raise RuntimeError("PyYAML is required to load packages from files")

    machine = utils.get_env("MACHINE", Path)
    machine_id = utils.get_env("MACHINE_ID", str)

    source_path = machine / "config" / "scripts"  # base
    if source == "machine":
        source_path = machine / "machines" / machine_id / "scripts"

    source_path = source_path / "packages.yaml"
    print(f"loading packages from: {source_path}")
    source_data = source_path.read_text()

    try:
        data: dict[str, dict[str, list[str]]] = yaml.safe_load(source_data)
        return data.get(source, {})
    except yaml.YAMLError as e:
        raise ValueError(f"invalid packages.yaml: {e}") from e


def filter_packages(
    packages: dict[str, list[Any]],
) -> dict[utils.PackageManager, list[Any]]:
    filtered: dict[utils.PackageManager, list[Any]] = {}
    for manager, _ in packages.items():
        pkg_manager = utils.PackageManager(manager)

        if not pkg_manager.is_supported():
            print(f"skipping unsupported package manager: {manager}")
            continue

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
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    args = parser.parse_args()
    utils.script_entrypoint("pkgs", main)
