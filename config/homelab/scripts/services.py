#!/usr/bin/env python3
"""Deploy homelab Compose projects from their repository directories."""

import os
import shutil
import subprocess
import time
from pathlib import Path

from app.env import ROOT


def main() -> None:
    """Deploy all shared and selected machine Compose projects."""
    # Locate the shared and machine-specific services.
    docker_directories = [
        Path(__file__).resolve().parent.parent / "docker",
        ROOT / "machines" / os.environ["MC_ID"] / "docker",
    ]

    services = [
        service.absolute()
        for directory in docker_directories
        if directory.is_dir()
        for service in sorted(directory.iterdir())
        if service.is_dir() and not service.name.startswith((".", "_"))
    ]

    # Wait for Docker daemon to be ready (Docker Desktop can be slow to start).
    _wait_for_docker()

    # Deploy each Compose project from its repository directory.
    for service in services:
        if not (service / "compose.yaml").is_file():
            continue

        print(f"deploying {service.name}...", flush=True)
        command = ["docker", "compose"]
        if (service / "secrets.env").is_file():
            command = ["op", "run", "--env-file=secrets.env", "--", *command]

        subprocess.run([*command, "pull", "--ignore-pull-failures"], cwd=service, check=True)
        subprocess.run(
            [*command, "up", "-d", "--build", "--remove-orphans"],
            cwd=service,
            check=True,
        )

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
