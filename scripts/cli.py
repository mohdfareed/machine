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


def main(debug: bool, dry_run: bool, args: list[str]) -> None:
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

    if debug:
        print("debug mode")
    if debug and dry_run:
        print("dry run mode")

    print(f"machine_id: {machine_id}")
    print(f"machine: {machine}")

    if debug:
        print(f"scripts: {scripts}")
        print(f"machine_shared: {machine_shared}")
        print(f"shared_scripts: {shared_scripts}")
        print(f"machine_config: {machine_config}")
        if machine_scripts.exists():
            print(f"machine_scripts: {machine_scripts}")
        print(f"args: {json.dumps(args, indent=2)}")


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
        main(args.debug, args.dry_run, extra)
        sys.exit(0)

    except KeyboardInterrupt:
        print("aborted!")
        sys.exit(1)

    except subprocess.CalledProcessError as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)

# endregion
