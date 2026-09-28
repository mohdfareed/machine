#!/usr/bin/env python3
"""Deploy the homelab's single Compose project."""

import os
import shutil
import subprocess
import time
from pathlib import Path


def main() -> None:
    """Check storage, then deploy services with their vault references."""

    # Refuse an unmounted share rather than writing media into an empty local folder.
    media = Path(os.environ["MC_HOMELAB_MEDIA_DIR"])
    if not media.is_mount():
        raise FileNotFoundError(f"Mount the PC's Media share at {media} before deployment")
    for name in ("movies", "series", "anime", "downloads"):
        if not (media / name).is_dir():
            raise FileNotFoundError(f"Media directory missing: {media / name}")

    # Prepare the local state root; Compose creates each app's bind directories.
    storage = Path(os.environ["MC_HOMELAB_STORAGE_DIR"])
    if not storage.parent.is_dir():
        raise FileNotFoundError(f"Storage parent missing: {storage.parent}")
    storage.mkdir(exist_ok=True)

    # Wait for Docker Desktop, then let Compose own networking and service startup.
    _wait_for_docker()
    directory = Path(__file__).resolve().parent.parent / "docker"
    command = ["op", "run", "--env-file=secrets.env", "--", "docker", "compose"]
    print("deploying homelab...", flush=True)
    subprocess.run([*command, "pull", "--ignore-pull-failures"], cwd=directory, check=True)
    subprocess.run([*command, "up", "-d", "--build", "--remove-orphans"], cwd=directory, check=True)
    print("all services deployed.")


def _wait_for_docker() -> None:
    if not shutil.which("docker"):
        raise FileNotFoundError("docker not found")

    print("waiting for docker daemon...", flush=True)
    for attempt in range(30):
        result = subprocess.run(
            ["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
        )
        if result.returncode == 0:
            return
        if attempt < 29:
            time.sleep(2)
    raise RuntimeError("docker daemon not available")


if __name__ == "__main__":
    main()
