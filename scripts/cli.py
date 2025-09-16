#!/usr/bin/env python3
"""
Machine setup CLI tool.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import utils


def main(dry_run: bool, args: list[str]) -> None:
    """CLI entry point."""
    machine = Path(os.environ.get("MACHINE", ""))
    machine_id = os.environ.get("MACHINE_ID", "")
    machine_shared = Path(os.environ.get("MACHINE_SHARED", ""))
    machine_config = Path(os.environ.get("MACHINE_CONFIG", ""))

    if not machine:
        raise RuntimeError("MACHINE environment variable is not set")
    if not machine_id:
        raise RuntimeError("MACHINE_ID environment variable is not set")
    if not machine_shared:
        raise RuntimeError("MACHINE_SHARED environment variable is not set")
    if not machine_config:
        raise RuntimeError("MACHINE_CONFIG environment variable is not set")

    scripts = machine / "scripts"
    shared_scripts = machine_shared / "scripts"
    machine_scripts = machine_config / "scripts"

    utils.debug("cli", "debug mode enabled")
    if dry_run:
        utils.debug("cli", "dry run mode enabled")

    print(f"machine_id: {machine_id}")
    print(f"machine: {machine}")

    utils.debug("cli", f"scripts: {scripts}")
    utils.debug("cli", f"machine_shared: {machine_shared}")
    utils.debug("cli", f"shared_scripts: {shared_scripts}")
    utils.debug("cli", f"machine_config: {machine_config}")
    if machine_scripts.exists():
        utils.debug("cli", f"machine_scripts: {machine_scripts}")
    utils.debug("cli", f"args: {json.dumps(args, indent=2)}")


# region: CLI

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # setup options
    parser.add_argument(
        "--debug", "-d", action="store_true", help="print debug information"
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="perform a dry run without making any changes",
    )

    # set environment
    args, extra = parser.parse_known_args()

    if args.debug:
        os.environ["DEBUG"] = "1"
    if args.dry_run:
        os.environ["DRY_RUN"] = "1"

    try:  # run setup script
        main(args.dry_run, extra)
        sys.exit(0)

    except KeyboardInterrupt:
        print("aborted!")
        sys.exit(1)

    except subprocess.CalledProcessError as error:
        utils.error(f"cli: {error}")
        sys.exit(1)

    except Exception as error:
        utils.error(f"cli: {error}")
        if os.environ.get("DEBUG"):
            raise
        sys.exit(1)

# endregion
