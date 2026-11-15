"""Sync canonical repository changes and refresh the installed CLI."""

from typing import Annotated

import typer

from app.runtime import env, reporting
from app.runtime.shell import query, run

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
        [
            *git,
            "-c",
            "fetch.recurseSubmodules=false",
            "fetch",
            "--no-tags",
            _CANONICAL_REPO_URL,
            "refs/heads/main",
        ],
        env=process_env,
        dry_run=dry_run,
        check=True,
    )
    run(
        [*git, "-c", "submodule.recurse=false", "merge", "--ff-only", "--autostash", "FETCH_HEAD"],
        env=process_env,
        dry_run=dry_run,
        check=True,
    )

    # Read actual conflicts; a successful merge may still leave autostash conflicts.
    result = query([*git, "ls-files", "--unmerged"], env=process_env)
    if result.stdout:
        raise RuntimeError("Could not restore local changes without conflicts")

    # Initialize empty submodules without moving existing checkouts.
    _sync_submodules(git, process_env, dry_run)

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


def _sync_submodules(git: list[str], process_env: dict[str, str], dry_run: bool) -> None:
    result = query([*git, "ls-tree", "-r", "-z", "HEAD"], env=process_env)
    for entry in result.stdout.split("\0"):
        if not entry:
            continue
        metadata, path = entry.split("\t", 1)
        mode, _, commit = metadata.split()
        if mode != "160000":
            continue

        staged = query([*git, "ls-files", "--stage", "-z", "--", path], env=process_env)
        if staged.stdout != f"160000 {commit} 0\t{path}\0":
            reporting.warning(f"Skipping submodule {path}: its recorded commit has staged changes.")
            continue

        directory = env.ROOT / path
        if (directory / ".git").exists():
            head = query(["git", "-C", str(directory), "rev-parse", "HEAD"], env=process_env)
            if head.stdout.strip() != commit:
                reporting.warning(
                    f"Skipping submodule {path}: checkout differs from recorded commit {commit}. "
                    "Deployment will use the existing checkout."
                )
            continue

        if directory.exists() and (not directory.is_dir() or any(directory.iterdir())):
            raise RuntimeError(
                f"Submodule path {path} is not empty; preserve its contents "
                "and initialize it manually."
            )
        run(
            [*git, "submodule", "update", "--init", "--checkout", "--", path],
            env=process_env,
            dry_run=dry_run,
            check=True,
        )
