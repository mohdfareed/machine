#!/usr/bin/env python3
"""Provision ``~/.env`` from env files in MC_PRIVATE.

Two modes:

1. **Explicit** — ``MC_ENV_FILES`` is set (space-separated list).  Each name
   maps to ``MC_PRIVATE/env/<name>.env``.  Files are concatenated in order.
2. **Simple** — ``MC_ENV_FILES`` is unset.  Falls back to ``MC_PRIVATE/.env``
   if it exists.

Output is written to ``~/.env`` (mode 600).
Skips silently when MC_PRIVATE is unset or no matching files are found.
"""

import os
import stat
from pathlib import Path

TARGET = Path.home() / ".env"


# ─── Source Resolution ────────────────────────────────────────────────────────


def resolve_env_sources(private_dir: Path, env_files: str | None) -> list[Path]:
    """Return the ordered list of env files to concatenate.

    When *env_files* is set (space-separated names), look up each
    ``<name>.env`` in ``<private_dir>/env/``.  Otherwise fall back
    to ``<private_dir>/.env``.
    """
    if env_files:
        env_dir = private_dir / "env"
        if not env_dir.is_dir():
            return []
        paths: list[Path] = []
        for name in env_files.split():
            path = env_dir / f"{name}.env"
            if path.is_file():
                paths.append(path)
        return paths

    # Fallback: single .env at root of MC_PRIVATE
    root_env = private_dir / ".env"
    return [root_env] if root_env.is_file() else []


# ─── Main ────────────────────────────────────────────────────────────────────


def main() -> None:
    private_path = os.environ.get("MC_PRIVATE", "").strip()
    if not private_path:
        print("env: MC_PRIVATE is not set, skipping")
        return

    private_dir = Path(os.path.expandvars(private_path)).expanduser()
    env_files = os.environ.get("MC_ENV_FILES", "").strip() or None

    matches = resolve_env_sources(private_dir, env_files)
    if not matches:
        mode = f"MC_ENV_FILES={env_files}" if env_files else f"{private_dir}/.env"
        print(f"env: no env files found ({mode})")
        return

    # Concatenate all matching files into ~/.env
    parts = [f.read_text() for f in matches]
    if TARGET.is_symlink() or TARGET.exists():
        TARGET.unlink()
    TARGET.write_text("\n".join(parts))
    TARGET.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 600

    names = [f.name for f in matches]
    print(f"env: {' + '.join(names)} -> {TARGET}")


if __name__ == "__main__":
    main()
