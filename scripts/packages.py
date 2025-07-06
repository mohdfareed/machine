#!/usr/bin/env python3
"""
Cross-platform package installer.
Reads JSON from CHEZMOI_PACKAGES and installs packages using
the specified package managers.
"""

import json
import os
import sys


def main() -> None:
    base = load_packages("base")
    machine = load_packages("machine")

    for manager, pkgs in {**base, **machine}.items():
        for pkg in pkgs:
            print(f"{manager}: {pkg}")  # TODO: implement installation logic


def load_packages(source: str) -> dict[str, list[str]]:
    try:
        data = json.loads(os.environ.get("CHEZMOI_PACKAGES", ""))
        return data.get(source, {}).get("packages", {})
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid CHEZMOI_PACKAGES: {e}") from e


if __name__ == "__main__":
    try:  # Run script
        main()
    except KeyboardInterrupt:
        print("aborted!")
        sys.exit(1)
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)
