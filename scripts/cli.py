#!/usr/bin/env python3
"""
Machine setup CLI tool.
"""

import argparse
import json
import os
import subprocess
from pathlib import Path

import utils


def main(dry_run: bool, args: list[str]) -> None:
    """CLI entry point."""
    utils.debug("cli", "debug mode enabled")
    if dry_run:
        utils.debug("cli", "dry run mode enabled")

    # read machine env
    machine = Path(os.environ.get("MACHINE", ""))
    machine_id = os.environ.get("MACHINE_ID", "")
    machine_shared = Path(os.environ.get("MACHINE_SHARED", ""))
    machine_config = Path(os.environ.get("MACHINE_CONFIG", ""))

    # validate env
    if not machine:
        raise RuntimeError("MACHINE environment variable is not set")
    if not machine_id:
        raise RuntimeError("MACHINE_ID environment variable is not set")
    if not machine_shared:
        raise RuntimeError("MACHINE_SHARED environment variable is not set")
    if not machine_config:
        raise RuntimeError("MACHINE_CONFIG environment variable is not set")

    # debug info
    print(f"machine_id: {machine_id}")
    print(f"machine: {machine}")
    utils.debug("cli", f"machine_shared: {machine_shared}")
    utils.debug("cli", f"machine_config: {machine_config}")
    utils.debug("cli", f"arguments: {json.dumps(args, indent=2)}")

    run_scripts(
        machine, machine_shared, machine_config
    )  # FIXME: implement subcommands

    # run setup
    argv = " ".join(args)
    update(machine, argv, dry_run)


def update(machine: Path, args: str, dry_run: bool) -> None:
    try:
        print("updating machine...")
        utils.run("git pull")
    except subprocess.CalledProcessError:
        ...

    print("initializing machine...")
    mode = "--apply" if not dry_run else "--dry-run"
    utils.run(f'chezmoi init {mode} --source "{str(machine)}" {args}')


def run_scripts(
    machine: Path, machine_shared: Path, machine_config: Path
) -> None:

    # resolve scripts paths
    scripts = machine / "scripts"
    shared_scripts = machine_shared / "scripts"
    machine_scripts = machine_config / "scripts"

    # debug info
    utils.debug("cli", f"scripts: {scripts}")
    utils.debug("cli", f"shared_scripts: {shared_scripts}")
    if machine_scripts.exists():
        utils.debug("cli", f"machine_scripts: {machine_scripts}")
    utils.debug("cli", f"args: {json.dumps(args, indent=2)}")


# region: CLI

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--debug", "-d", action="store_true", help="print debug information"
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="perform a dry run without making any changes",
    )

    args, extra = parser.parse_known_args()
    if args.debug:
        os.environ["DEBUG"] = "1"
    if args.dry_run:
        os.environ["DRY_RUN"] = "1"
    utils.script_entrypoint("cli", lambda: main(args.dry_run, extra))

# endregion
