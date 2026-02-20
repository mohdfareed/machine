#!/usr/bin/env python3
"""SSH key provisioning.

Copies private keys from MC_PRIVATE to ~/.ssh/ and registers
them with the SSH agent. Skips silently if MC_PRIVATE is unset
or the path doesn't exist. Never overwrites keys that are already
in place.

MC_PRIVATE should point to a directory containing keys directly,
or a subdirectory named ssh/ or .ssh/. Each key is a file without the
.pub extension; the matching .pub file is optional.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

SSH_DIR = Path.home() / ".ssh"


def main() -> None:
    private_path = os.environ.get("MC_PRIVATE", "").strip()
    if not private_path:
        print("ssh: MC_PRIVATE is not set; skipping SSH setup", file=sys.stderr)
        return  # module not configured for this machine

    private_root = Path(os.path.expandvars(private_path)).expanduser()
    if not private_root.exists():
        print(
            f"ssh: MC_PRIVATE path does not exist: {private_root}\n"
            f"  Copy your keys to this path before running setup.\n"
            f"  Example: scp -r <source>/private <host>:{private_root}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Locate the keys directory: prefer ssh/ or .ssh/ subdirectory
    for subdir in ("ssh", ".ssh", ""):
        candidate = private_root / subdir if subdir else private_root
        if candidate.is_dir():
            keys_dir = candidate
            break
    else:
        print(f"ssh: no keys directory found under {private_root}", file=sys.stderr)
        return

    # Collect private key files (no .pub extension, not a directory)
    private_keys = [f for f in keys_dir.iterdir() if f.is_file() and f.suffix != ".pub"]
    if not private_keys:
        return

    # Ensure ~/.ssh exists with correct permissions
    SSH_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)

    for key in private_keys:
        dest = SSH_DIR / key.name
        if dest.exists():
            continue  # never overwrite

        shutil.copy2(key, dest)
        dest.chmod(0o600)
        print(f"ssh: installed {key.name}")

        # Copy matching public key if present
        pub = key.with_suffix(".pub")
        if pub.exists():
            dest_pub = SSH_DIR / pub.name
            if not dest_pub.exists():
                shutil.copy2(pub, dest_pub)
                dest_pub.chmod(0o644)

        # Add to agent
        is_macos = sys.platform.startswith("darwin")
        add_cmd = ["ssh-add"]
        if is_macos:
            add_cmd += ["--apple-use-keychain"]
        add_cmd.append(str(dest))
        subprocess.run(add_cmd, check=False)


if __name__ == "__main__":
    main()
