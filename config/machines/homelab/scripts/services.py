#!/usr/bin/env python3
"""Deploy the Compose projects directly under the homelab Docker directory."""

import os
import shutil
import subprocess
import time
from pathlib import Path

from _onepassword import deployment_environment, replace_token

# =============================================================================
# MARK: Deploy services
# =============================================================================


def main() -> None:
    """Check storage, then deploy services with their vault references."""

    # Require a mounted volume so missing storage cannot fall back to the internal disk.
    media = Path(os.environ["MC_HOMELAB_MEDIA_DIR"])
    volume = media.resolve()
    while volume.parent != Path("/Volumes") and volume != volume.parent:
        volume = volume.parent
    if volume.parent != Path("/Volumes") or not volume.is_mount():
        raise FileNotFoundError(f"Mount the volume containing {media} before deployment")
    media_directories = (
        "movies",
        "series",
        "anime",
        "downloads",
    )
    for name in media_directories:
        if not (media / name).is_dir():
            raise FileNotFoundError(f"Media directory missing: {media / name}")

    # Prepare the local state root; Compose creates each app's bind directories.
    storage = Path(os.environ["MC_HOMELAB_STORAGE_DIR"])
    if not storage.parent.is_dir():
        raise FileNotFoundError(f"Storage parent missing: {storage.parent}")

    # Authenticate once; each op run starts from the same uninjected environment.
    environment = deployment_environment()
    directory = Path(__file__).resolve().parent.parent / "docker"
    projects = sorted(
        compose
        for compose in directory.glob("*/compose.yaml")
        if not compose.parent.name.startswith(".")
    )

    commands = []
    for compose in projects:
        project = compose.parent

        # Let the CLI resolve only this project's references and Environments.
        command = ["op", "run"]
        if (project / "secrets.env").is_file():
            command.append("--env-file=secrets.env")
        for line in (project / "env.txt").read_text().splitlines():
            environment_id = line.strip()
            if environment_id and not environment_id.startswith("#"):
                command.extend(["--environment", environment_id])

        commands.append((compose, command))

    # A no-op child makes loading failures distinct from Docker command failures.
    while True:
        for compose, command in commands:
            result = subprocess.run(
                [*command, "--", "/usr/bin/true"],
                cwd=compose.parent,
                env=environment,
                check=False,
            )
            if result.returncode:
                print(f"1Password could not load secrets for {compose.parent.name}.", flush=True)
                replace_token(environment)
                break  # Recheck every project's access with the replacement token.
        else:
            break

    # Make runtime changes only after every project's secrets can load.
    storage.mkdir(exist_ok=True)

    # Wait for Docker Desktop before preparing deployment.
    _wait_for_docker()

    # Share one network across independently managed projects.
    network = subprocess.run(
        ["docker", "network", "inspect", "homelab"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if network.returncode:
        subprocess.run(["docker", "network", "create", "homelab"], check=True)

    print("deploying homelab...", flush=True)
    for compose, load_command in commands:
        project = compose.parent

        # Scope Compose to this file and its declared project name, without the token.
        command = [*load_command]
        command.extend(
            [
                "--",
                "env",
                "-u",
                "OP_SERVICE_ACCOUNT_TOKEN",
                "-u",
                "COMPOSE_PROJECT_NAME",
                "docker",
                "compose",
                "--file",
                str(compose),
            ]
        )

        print(f"deploying {project.name}...", flush=True)
        subprocess.run(
            [*command, "pull", "--ignore-pull-failures"], cwd=project, env=environment, check=True
        )
        subprocess.run([*command, "up", "-d", "--build"], cwd=project, env=environment, check=True)

    print("all services deployed.")


# =============================================================================
# MARK: Wait for Docker
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


if __name__ == "__main__":
    main()
