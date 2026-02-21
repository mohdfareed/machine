#!/usr/bin/env python3
"""Symlink private env files into well-known shell paths.

Creates symlinks so shell configs can source a fixed path without
needing MC_PRIVATE at startup.
Skips silently when MC_PRIVATE is unset or the source files do not
exist.
"""

import os
from pathlib import Path

HOME = Path.home()
TARGETS = {
    "env.sh": HOME / ".env",
    "env.ps1": HOME / ".env.ps1",
}


def main() -> None:
    private_path = os.environ.get("MC_PRIVATE", "").strip()
    if not private_path:
        print("env: MC_PRIVATE is not set, skipping")
        return

    private_root = Path(os.path.expandvars(private_path)).expanduser()
    for filename, target in TARGETS.items():
        source = private_root / filename
        if not source.is_file():
            continue

        if target.is_symlink() or target.exists():
            target.unlink()
        target.symlink_to(source)

        source.chmod(0o600)
        print(f"env: {source} -> {target}")


if __name__ == "__main__":
    main()
