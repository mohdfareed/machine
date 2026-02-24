#!/usr/bin/env python3
"""Symlink per-machine env file into ~/.env.

Source: ``MC_PRIVATE/env/<MC_ID>.env``
Target: ``~/.env``

Skips silently when MC_PRIVATE is unset or the source file does not exist.
"""

import os
from pathlib import Path

SYMLINK = Path.home() / ".env"


def main() -> None:
    private_path = os.environ.get("MC_PRIVATE", "").strip()
    if not private_path:
        print("env: MC_PRIVATE is not set, skipping")
        return

    machine_id = os.environ.get("MC_ID", "").strip()
    if not machine_id:
        print("env: MC_ID is not set, skipping")
        return

    source = Path(os.path.expandvars(private_path)).expanduser() / "env" / f"{machine_id}.env"
    if not source.is_file():
        print(f"env: {source} does not exist, skipping")
        return

    if SYMLINK.is_symlink() or SYMLINK.exists():
        SYMLINK.unlink()

    SYMLINK.symlink_to(source)
    SYMLINK.chmod(0o600)
    print(f"env: {SYMLINK} -> {source}")


if __name__ == "__main__":
    main()
