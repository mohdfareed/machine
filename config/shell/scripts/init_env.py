#!/usr/bin/env python3
"""Provision dotenv files from MC_PRIVATE.

Builds ``~/.env`` by concatenating:

1. ``MC_PRIVATE/machine.env``    — shared secrets (OPENAI_API_KEY, etc.)
2. ``MC_PRIVATE/<MC_ID>.env``    — machine-specific overrides (optional)

This mirrors the Docker ``.env`` concatenation pattern: shared keys
defined once, machine-specific keys layered on top.

Skips silently when MC_PRIVATE is unset or the source files do not exist.
"""

import os
import stat
from pathlib import Path

SHARED_NAME = "machine.env"
TARGET = Path.home() / ".env"


def main() -> None:
    private_path = os.environ.get("MC_PRIVATE", "").strip()
    if not private_path:
        print("env: MC_PRIVATE is not set, skipping")
        return

    private_root = Path(os.path.expandvars(private_path)).expanduser() / "env"
    if not private_root.is_dir():
        print(f"env: {private_root} does not exist, skipping")
        return

    machine_id = os.environ.get("MC_ID", "").strip()
    shared = private_root / SHARED_NAME
    machine = private_root / f"{machine_id}.env" if machine_id else None

    has_shared = shared.is_file()
    has_machine = machine is not None and machine.is_file()

    if not has_shared and not has_machine:
        print("env: no env files found, skipping")
        return

    # Concatenate shared + per-machine into ~/.env
    parts: list[str] = []
    if has_shared:
        parts.append(shared.read_text())
    if has_machine:
        parts.append(machine.read_text())  # type: ignore[union-attr]

    if TARGET.is_symlink() or TARGET.exists():
        TARGET.unlink()
    TARGET.write_text("\n".join(parts))
    TARGET.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 600

    sources = [s for s in [SHARED_NAME, f"{machine_id}.env"] if (private_root / s).is_file()]
    print(f"env: {' + '.join(sources)} -> {TARGET}")


if __name__ == "__main__":
    main()
