#!/usr/bin/env python3
"""
SSH setup and key management.

- Ensures ~/.ssh directory and permissions
- Copies keys from MACHINE_PRIVATE (ssh/ or .ssh/) into ~/.ssh
- Fixes file permissions (600 private, 644 public, 600 config/authorized_keys)
- Builds/updates authorized_keys from available public keys
- Adds private keys to SSH agent (macOS: --apple-use-keychain)

Idempotent and safe by default: will not overwrite existing key files.
Respects DEBUG and DRY_RUN environment variables.
"""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

import utils


def ensure_dir(path: Path) -> None:
    if path.exists():
        return
    if not path.is_dir():
        raise RuntimeError(f"path is not a directory: {path}")

    utils.debug("ssh", f"creating directory: {path}")
    if not os.environ.get("DRY_RUN"):
        path.mkdir(parents=True, exist_ok=True)


def set_permissions(path: Path, mode: int) -> None:
    if utils.WINDOWS:
        return  # rely on default ACLs on Windows

    try:
        if not os.environ.get("DRY_RUN"):
            os.chmod(path, mode)
    except PermissionError:
        utils.debug("ssh", f"chmod skipped (permission denied): {path}")


def is_private_key(file: Path) -> bool:
    try:  # read file content
        private_key = file.read_text().strip().splitlines()
    except Exception:
        return False

    # must have at least two lines
    if len(private_key) < 2:
        return False

    # check for private key delimiters
    starts = private_key[0].startswith("-----BEGIN")
    ends = private_key[0].endswith("PRIVATE KEY-----")
    return starts and ends


def get_private_keys(private_root: Path) -> list[Path]:
    sources = [private_root / "ssh", private_root / ".ssh", private_root]
    paths: list[Path] = []
    for source in sources:
        if source.exists() and source.is_dir():
            for file in source.iterdir():
                if is_private_key(file):
                    paths.append(file)
    return paths


def copy_key(key: Path, ssh_dir: Path, mode: int) -> None:
    dest = ssh_dir / key.name

    if dest.exists():
        print(f"key exists, skipping: {dest}")
        return
    elif not key.exists():
        print(f"key not found, skipping: {key}")
        return

    print(f"copying key: {key} -> {dest}")
    if not os.environ.get("DRY_RUN"):
        shutil.copy2(key, dest)
    set_permissions(dest, mode)


def add_keys_to_agent(private_keys: list[Path]) -> None:
    if not private_keys:
        print("no private keys found to add to agent")
        return
    if os.environ.get("DRY_RUN"):
        return

    if utils.MACOS:
        for key in private_keys:
            utils.run(f'ssh-add --apple-use-keychain "{str(key)}"')
    else:
        for key in private_keys:
            utils.run(f'ssh-add "{str(key)}"')


def main(path: str) -> None:
    private_root = path or os.environ.get("MACHINE_PRIVATE")
    if not private_root:
        raise RuntimeError("MACHINE_PRIVATE environment variable is not set")
    private_root = Path(private_root).expanduser()

    ssh_dir = Path.home() / ".ssh"
    ensure_dir(ssh_dir)
    set_permissions(ssh_dir, 0o700)

    cfg = ssh_dir / "config"
    if cfg.exists():
        set_permissions(cfg, 0o600)

    print("setting up ssh...")
    utils.debug("ssh", f"private_root: {private_root}")
    utils.debug("ssh", f"ssh_dir: {ssh_dir}")

    for private_key in get_private_keys(private_root):
        public_key = private_key.with_suffix(".pub")
        copy_key(private_key, ssh_dir, 0o600)
        copy_key(public_key, ssh_dir, 0o644)

    private_keys = [
        p for p in ssh_dir.iterdir() if p.is_file() and is_private_key(p)
    ]
    add_keys_to_agent(private_keys)
    print("ssh setup complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=str)
    args = parser.parse_args()
    utils.script_entrypoint("ssh.py", lambda: main(args.path or ""))
