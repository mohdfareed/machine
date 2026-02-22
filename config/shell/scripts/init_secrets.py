#!/usr/bin/env python3
"""Symlink private env file into ~/.env."""

import os
from pathlib import Path

# DOTENV_SOURCE -> DOTENV_TARGET
DOTENV_TARGET = "secrets.env"  # symlink target
DOTENV_SOURCE = Path.home() / ".env"  # symlink source


def main() -> None:
    private_path = os.environ.get("MC_PRIVATE", "").strip()
    if not private_path:
        print("env: MC_PRIVATE is not set, skipping")
        return  # no private root, skip

    # resolve private config root
    private_root = Path(os.path.expandvars(private_path)).expanduser()
    target = private_root / DOTENV_TARGET

    if not target.is_file():
        print(f"env: {target} does not exist, skipping")
        return  # no symlink target, skip

    # clean up symlink source if it already exists
    if DOTENV_SOURCE.is_symlink() or DOTENV_SOURCE.exists():
        DOTENV_SOURCE.unlink()

    # create symlink and set permissions
    DOTENV_SOURCE.symlink_to(target)
    DOTENV_SOURCE.chmod(0o600)

    print(f"env: {DOTENV_SOURCE} -> {target}")


if __name__ == "__main__":
    main()
