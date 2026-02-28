#!/usr/bin/env python3
"""SSH key provisioning from MC_PRIVATE."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

SSH_DIR = Path.home() / ".ssh"


def main() -> None:
    private_root = Path(os.environ["MC_PRIVATE"]).expanduser()
    if not private_root.is_dir():
        print(f"ssh: {private_root} does not exist, skipping key provisioning")
        return

    # Locate the keys directory: prefer ssh/ or .ssh/ subdirectory
    keys_dir = private_root
    for subdir in ("ssh", ".ssh"):
        candidate = private_root / subdir
        if candidate.is_dir():
            keys_dir = candidate
            break

    # Look for a key named after the machine ID
    machine_id = os.environ.get("MC_ID", "").strip()
    if not machine_id:
        print("ssh: MC_ID is not set, skipping key provisioning", file=sys.stderr)
        sys.exit(1)

    key_file = keys_dir / machine_id
    if not key_file.is_file():
        print(
            f"ssh: key '{machine_id}' not found in {keys_dir}\n"
            f"  Create {key_file} before running setup again.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Ensure ~/.ssh exists with correct permissions
    SSH_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    dest = SSH_DIR / key_file.name

    if not dest.exists():
        shutil.copy2(key_file, dest)
        dest.chmod(0o600)
        print(f"ssh: installed {key_file.name}")

        # Copy matching public key if present
        pub = key_file.with_suffix(".pub")
        if pub.exists():
            dest_pub = SSH_DIR / pub.name
            if not dest_pub.exists():
                shutil.copy2(pub, dest_pub)
                dest_pub.chmod(0o644)

    # Always register with agent
    add_cmd = ["ssh-add"]
    if sys.platform.startswith("darwin"):
        add_cmd += ["--apple-use-keychain"]
    add_cmd.append(str(dest))
    subprocess.run(add_cmd, check=False)


if __name__ == "__main__":
    main()
