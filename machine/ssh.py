"""SSH key management.

Handles:
- Creating ~/.ssh directory with correct permissions
- Copying keys from private path to ~/.ssh
- Setting correct permissions on keys
- Adding keys to SSH agent (with macOS Keychain support)
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from machine.core import MACOS, WINDOWS, debug, info, is_dry_run, run


def setup_ssh(private_path: Path | None = None) -> None:
    """Set up SSH keys from private path.

    Args:
        private_path: Path to directory containing SSH keys.
                     Searches: {path}/ssh/, {path}/.ssh/, {path}/
    """
    if private_path is None:
        info("ssh: no private path configured, skipping")
        return

    private_path = Path(private_path).expanduser()
    if not private_path.exists():
        info(f"ssh: private path not found: {private_path}")
        return

    ssh_dir = Path.home() / ".ssh"
    ensure_ssh_dir(ssh_dir)

    info("setting up SSH keys...")
    debug("ssh", f"private_path: {private_path}")
    debug("ssh", f"ssh_dir: {ssh_dir}")

    # Copy keys
    for private_key in find_private_keys(private_path):
        public_key = private_key.with_suffix(".pub")
        copy_key(private_key, ssh_dir, 0o600)
        copy_key(public_key, ssh_dir, 0o644)

    # Add to agent
    private_keys = [
        p for p in ssh_dir.iterdir() if p.is_file() and is_private_key(p)
    ]
    add_keys_to_agent(private_keys)

    info("SSH setup complete")


def ensure_ssh_dir(ssh_dir: Path) -> None:
    """Ensure ~/.ssh exists with correct permissions."""
    if not ssh_dir.exists():
        debug("ssh", f"creating: {ssh_dir}")
        if not is_dry_run():
            ssh_dir.mkdir(parents=True, exist_ok=True)

    set_permissions(ssh_dir, 0o700)

    # Fix config permissions if exists
    config = ssh_dir / "config"
    if config.exists():
        set_permissions(config, 0o600)


def set_permissions(path: Path, mode: int) -> None:
    """Set file permissions (no-op on Windows)."""
    if WINDOWS:
        return

    try:
        if not is_dry_run():
            os.chmod(path, mode)
    except PermissionError:
        debug("ssh", f"chmod skipped (permission denied): {path}")


def is_private_key(file: Path) -> bool:
    """Check if a file is an SSH private key."""
    try:
        lines = file.read_text().strip().splitlines()
    except Exception:
        return False

    if len(lines) < 2:
        return False

    first_line = lines[0]
    return first_line.startswith("-----BEGIN") and first_line.endswith(
        "PRIVATE KEY-----"
    )


def find_private_keys(private_root: Path) -> list[Path]:
    """Find all private keys in common locations."""
    search_paths = [
        private_root / "ssh",
        private_root / ".ssh",
        private_root,
    ]

    keys: list[Path] = []
    for path in search_paths:
        if path.exists() and path.is_dir():
            for file in path.iterdir():
                if file.is_file() and is_private_key(file):
                    keys.append(file)

    return keys


def copy_key(key: Path, ssh_dir: Path, mode: int) -> None:
    """Copy a key file to ~/.ssh if it doesn't exist."""
    dest = ssh_dir / key.name

    if dest.exists():
        debug("ssh", f"key exists, skipping: {dest}")
        return

    if not key.exists():
        debug("ssh", f"key not found: {key}")
        return

    info(f"copying key: {key.name}")
    if not is_dry_run():
        shutil.copy2(key, dest)
    set_permissions(dest, mode)


def add_keys_to_agent(private_keys: list[Path]) -> None:
    """Add private keys to SSH agent."""
    if not private_keys:
        debug("ssh", "no private keys to add to agent")
        return

    info(f"adding {len(private_keys)} keys to SSH agent")
    for key in private_keys:
        if MACOS:
            run(f'ssh-add --apple-use-keychain "{key}"', check=False)
        else:
            run(f'ssh-add "{key}"', check=False)
