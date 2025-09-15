#!/usr/bin/env python3
"""
Machine setup CLI tool.
"""

import argparse
import os
import subprocess
import sys


def main(args: list[str]) -> None:
    """CLI entry point."""
    print(f"machine cli tool: {args}")


# region: CLI

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # setup options
    parser.add_argument(
        "--debug", action="store_true", help="print debug information"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="print bootstrapping settings"
    )

    # set environment
    args, extra = parser.parse_known_args()
    if args.dry_run:
        os.environ["DRY_RUN"] = "1"
    if args.debug:
        os.environ["DEBUG"] = "1"

    try:  # run setup script
        main(extra)
        print("done!")
        sys.exit(0)

    except KeyboardInterrupt:
        print("aborted!")
        sys.exit(1)

    except subprocess.CalledProcessError as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)

# endregion
