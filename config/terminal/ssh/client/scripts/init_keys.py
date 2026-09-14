#!/usr/bin/env python3
"""Provision machine-specific SSH files from MC_PRIVATE."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

SSH_DIR = Path.home() / ".ssh"


def main() -> None:
    # Locate the machine's private SSH files.
    source_dir = Path(os.environ["MC_PRIVATE"]).expanduser() / "ssh"
    if not source_dir.is_dir():
        print(f"ssh: {source_dir} does not exist, skipping key provisioning")
        return

    # Prepare the SSH directory, install files, and load keys.
    SSH_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    _install_files(source_dir)
    _load_keys(source_dir)


def _install_files(source_dir: Path) -> None:
    # Select machine-specific key files for installation.
    for source in sorted(source_dir.iterdir()):
        if not source.is_file() or source.name == "config" or source.name.startswith("known_hosts"):
            continue

        # Replace managed symlinks with regular files.
        destination = SSH_DIR / source.name
        if destination.is_symlink():
            destination.unlink()

        # Install changed files and enforce platform permissions.
        if not destination.exists() or source.read_bytes() != destination.read_bytes():
            shutil.copy2(source, destination)
            print(f"ssh: installed {source.name}")

        _set_permissions(source, destination)


def _set_permissions(source: Path, destination: Path) -> None:
    # Apply standard SSH modes on Unix-like systems.
    if os.name != "nt":
        destination.chmod(0o644 if source.suffix == ".pub" else 0o600)
        return

    # Restrict Windows access to the current user and SYSTEM.
    user = f"{os.environ['USERDOMAIN']}\\{os.environ['USERNAME']}"
    commands = [
        ["icacls", destination, "/inheritance:r"],
        [
            "icacls",
            destination,
            "/grant:r",
            f"{user}:(F)",
            "*S-1-5-18:(F)",
        ],
    ]

    # Retry after replacing a destination whose ACL blocks access.
    for attempt in range(2):
        try:
            for command in commands:
                subprocess.run(
                    command,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            return
        except subprocess.CalledProcessError:
            if attempt == 1:
                raise

            # Replace the inaccessible destination before retrying.
            destination.unlink()
            shutil.copy2(source, destination)
            print(f"ssh: replaced inaccessible {source.name}")


def _load_keys(source_dir: Path) -> None:
    # Collect keys already present in the agent.
    loaded_keys = subprocess.run(
        ["ssh-add", "-L"],
        capture_output=True,
        check=False,
        text=True,
    )

    # Index loaded key blobs for comparison.
    loaded_blobs = {
        fields[1] for line in loaded_keys.stdout.splitlines() if len(fields := line.split()) >= 2
    }

    # Match public keys with their installed private keys.
    for public_key in sorted(source_dir.glob("*.pub")):
        private_key = SSH_DIR / public_key.stem
        if not private_key.is_file():
            continue  # Missing private key, skip loading.

        # Validate the public key before comparing its key blob.
        key_fields = public_key.read_text(encoding="utf-8").split()
        if len(key_fields) < 2:
            print(f"ssh: invalid public key: {public_key.name}", file=sys.stderr)
            continue
        if key_fields[1] in loaded_blobs:
            print(f"ssh: {private_key.name} already loaded")
            continue

        # Load missing keys with the platform-specific agent options.
        command = ["ssh-add"]
        if sys.platform.startswith("darwin"):
            command.append("--apple-use-keychain")
        command.append(str(private_key))

        # Add the key and remember successful loads.
        result = subprocess.run(command, check=False)
        if result.returncode == 0:
            loaded_blobs.add(key_fields[1])


if __name__ == "__main__":
    main()
