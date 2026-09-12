"""Sync canonical repository changes and deploy the current machine."""

import logging
import subprocess

import typer

from app import reporting
from app.cli.deploy import deploy
from app.cli.entry import get_current_machine
from app.env import settings

_logger = logging.getLogger(__name__)
_CANONICAL_REPO_URL = "https://github.com/mohdfareed/machine.git"

# =============================================================================
# MARK: Sync Command
# =============================================================================


def sync(
    no_deploy: bool = typer.Option(
        False, "--no-deploy", help="Skip deployment after repository integration."
    ),
) -> None:
    """Sync repo changes and deploy the current checkout."""

    if settings.dry_run:
        reporting.heading("Plan")
        reporting.detail(f"Fetch main from {_CANONICAL_REPO_URL}")
        reporting.detail("Would merge canonical main with --ff-only --autostash.")
        reporting.detail("Would check for conflicts after restoring local changes.")
        return

    # Fetch and merge canonical main in the repo root.
    git = ["git", "-C", str(settings.home)]
    for heading, args in (
        (
            "Fetching canonical main",
            ["fetch", "--no-tags", _CANONICAL_REPO_URL, "refs/heads/main"],
        ),
        ("Merging canonical main", ["merge", "--ff-only", "--autostash", "FETCH_HEAD"]),
    ):
        reporting.heading(heading)
        result = subprocess.run([*git, *args], capture_output=True, text=True)
        if result.returncode != 0:
            _logger.debug("git %s failed:\n%s\n%s", " ".join(args), result.stdout, result.stderr)
            reporting.error("Git operation failed.")
            reporting.detail(f"See {settings.log_file} for details.", error=True)

            raise SystemExit(1)

    # Check for conflicts left by autostash restoration.
    # Autostash conflicts can leave the merge's exit code at zero.
    reporting.heading("Checking for conflicts")
    result = subprocess.run([*git, "ls-files", "--unmerged"], capture_output=True, text=True)
    if result.returncode != 0:
        _logger.debug("git ls-files failed:\n%s\n%s", result.stdout, result.stderr)
        reporting.error("Could not check for conflicts.")
        reporting.detail(f"See {settings.log_file} for details.", error=True)

        raise SystemExit(1)

    if result.stdout.strip():
        reporting.error("Could not restore local changes without conflicts.")
        reporting.detail("Resolve conflicts before deploying.", error=True)
        raise SystemExit(1)

    # Report the sync result and stop if deployment was skipped.
    reporting.success("Complete · canonical main.")
    if no_deploy:
        return

    # Deploy the current machine.
    machine_id = get_current_machine()
    deploy(machine=machine_id)
