"""Sync canonical repository changes and refresh the installed CLI."""

from typing import Annotated

import typer

from app import env, reporting
from app.shell import query, run

_CANONICAL_REPO_URL = "https://github.com/mohdfareed/machine.git"


def sync(
    dry_run: Annotated[
        bool, typer.Option("-n", "--dry-run", help="Preview changes without applying them.")
    ] = False,
) -> None:
    """Sync canonical main into the checkout and refresh the CLI installation."""
    if dry_run:
        reporting.heading("Dry run: no changes will be made.")

    process_env: dict[str, str] = {}
    git = ["git", "-C", str(env.ROOT)]
    reporting.debug(f"Canonical source: {_CANONICAL_REPO_URL} main")

    # Integrate canonical main without discarding local work.
    reporting.heading("Syncing repository")
    run(
        [*git, "fetch", "--no-tags", _CANONICAL_REPO_URL, "refs/heads/main"],
        env=process_env,
        dry_run=dry_run,
        check=True,
    )
    run(
        [*git, "merge", "--ff-only", "--autostash", "FETCH_HEAD"],
        env=process_env,
        dry_run=dry_run,
        check=True,
    )

    # Read actual conflicts; a successful merge may still leave autostash conflicts.
    result = query([*git, "ls-files", "--unmerged"], env=process_env)
    if result.stdout:
        raise RuntimeError("Could not restore local changes without conflicts")

    # Refresh the installed entry point.
    reporting.heading("Refreshing CLI")
    run(
        ["uv", "tool", "install", str(env.ROOT), "--editable", "--force"],
        env=process_env,
        dry_run=dry_run,
        check=True,
    )

    reporting.plain("")
    reporting.success("Complete.")
