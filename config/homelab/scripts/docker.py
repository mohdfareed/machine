#!/usr/bin/env python3
"""Link homelab service directories and deploy their Compose projects."""

import os
import shutil
import subprocess
import time
from pathlib import Path

# =============================================================================
# MARK: Deploy
# =============================================================================


def main() -> None:
    """Deploy the shared and selected machine's services using the inherited environment."""
    homelab_path = os.environ["MC_HOMELAB_DIR"]
    if not homelab_path:
        raise ValueError("MC_HOMELAB_DIR is required")

    # Locate the homelab deployment directory.
    homelab_dir = Path(homelab_path).resolve()
    docker_directories = [
        Path(__file__).resolve().parent.parent / "docker",
        Path(os.environ["MC_MACHINE"]) / "docker",
    ]

    services = [
        service.absolute()
        for directory in docker_directories
        if directory.is_dir()
        for service in sorted(directory.iterdir())
        if service.is_dir() and not service.name.startswith(".")
    ]

    # Wait for Docker daemon to be ready (Docker Desktop can be slow to start).
    _wait_for_docker()

    # Link homelab service directories without replacing real paths.
    homelab_dir.mkdir(parents=True, exist_ok=True)
    for service in services:
        _link_service(service, homelab_dir / service.name)

    # Deploy each Compose project from its repository directory.
    for service in services:
        if not (service / "compose.yaml").is_file():
            continue

        print(f"deploying {service.name}...", flush=True)
        subprocess.run(
            ["docker", "compose", "pull", "--ignore-pull-failures"], cwd=service, check=True
        )
        subprocess.run(
            ["docker", "compose", "up", "-d", "--build", "--remove-orphans"],
            cwd=service,
            check=True,
        )

    print("all services deployed.")


# =============================================================================
# MARK: Prepare Docker and Service Links
# =============================================================================


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


def _link_service(source: Path, link: Path) -> None:
    # Leave existing data for a separate migration.
    is_junction = link.is_junction()
    is_symlink = link.is_symlink()
    if link.exists(follow_symlinks=False) and not is_junction and not is_symlink:
        raise FileExistsError(
            f"cannot replace {link}; move or migrate the existing path before deploying"
        )

    # Remove only the link itself when its target has changed.
    if is_junction or is_symlink:
        if link.resolve() == source.resolve():
            return
        if is_junction:
            link.rmdir()
        else:
            link.unlink()

    # Use Unix symlinks and Windows directory junctions without elevation.
    if os.name != "nt":
        link.symlink_to(source, target_is_directory=True)
        return

    quoted_link = str(link).replace("'", "''")
    quoted_source = str(source).replace("'", "''")
    subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            f"New-Item -ItemType Junction -Path '{quoted_link}' "
            f"-Target '{quoted_source}' -ErrorAction Stop | Out-Null",
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
