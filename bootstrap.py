#!/usr/bin/env python3
"""
Deploy a new machine using Chezmoi.

Installs Chezmoi and bootstraps a new machine using the the official script at:
https://www.chezmoi.io/install/#one-line-binary-install
On macOS, Command Line Tools for Xcode are required. Install them using:
xcode-select --install
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Union

REPOSITORY = "mohdfareed/machine"
DEFAULT_BRANCH = "main"
DEFAULT_MACHINE_PATH = Path.home() / ".machine"
CHEZMOI = f'sh -c "$(curl -fsLS get.chezmoi.io)" --'


def main(path: Path, branch: str, dry_run: bool) -> None:
    """Install application."""
    repo = f"git@github.com:{REPOSITORY}.git"
    options = f"--branch {branch} --source {path}"

    print(f"Deploying machine to: {path}")
    if dry_run:
        run(f"{CHEZMOI} init --apply {repo} {options} --dry-run")
    else:
        run(f"{CHEZMOI} init --apply {repo} {options}")
    print("Machine deployed successfully.")


def run(cmd: Union[str, list[str]]) -> subprocess.CompletedProcess[bytes]:
    cmd = cmd if isinstance(cmd, str) else " ".join(cmd)
    return subprocess.run(cmd, shell=True, check=True)


# region: CLI

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-p",
        "--path",
        type=Path,
        help="machine installation path",
        default=DEFAULT_MACHINE_PATH,
    )
    parser.add_argument(
        "-b",
        "--branch",
        type=str,
        help="machine repo branch",
        default=DEFAULT_BRANCH,
    )
    parser.add_argument("--dry-run", action="store_true", help="dry run")
    args = parser.parse_args()

    try:  # Run script
        main(args.path, args.branch, args.dry_run)
    except KeyboardInterrupt:
        print("Aborted!")
        sys.exit(1)
    except subprocess.CalledProcessError as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

# endregion
