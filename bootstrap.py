#!/usr/bin/env python3
"""
Deploy a new machine using Chezmoi.

Installs Chezmoi and bootstraps a new machine using the the official script at:
https://www.chezmoi.io/install/#one-line-binary-install
On macOS, Command Line Tools for Xcode are required. Install them using:
xcode-select --install
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

REPOSITORY = "mohdfareed/machine"
DEFAULT_BRANCH = "dev-refactor"  # FIXME: switch to main
DEFAULT_MACHINE_PATH = Path.home() / ".machine"
CHEZMOI = f'sh -c "$(curl -fsLS get.chezmoi.io)" --'


def main(
    bin: Path, path: Path, branch: str, local: bool, dry_run: bool
) -> None:
    """Install application."""
    path = path.expanduser().resolve()
    bin = bin.expanduser().resolve()

    repo = f"git@github.com:{REPOSITORY}.git"
    chezmoi = f"{CHEZMOI} -b {bin}"
    if shutil.which("chezmoi"):
        chezmoi = "chezmoi"

    options = f"--source {path}"
    if not local:
        options += f" --branch {branch} {repo}"
    if dry_run:
        options += f" --dry-run"

    print(f"bootstrapping machine at: {path}")
    run(f"{chezmoi} init --apply {options}")
    print("machine bootstrapped successfully")


def run(cmd: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(cmd, shell=True, check=True)


# region: CLI

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "path",
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
    parser.add_argument("--local", action="store_true", help="use local repo")
    args = parser.parse_args()

    try:  # Run script
        with TemporaryDirectory() as tempdir:
            main(
                Path(tempdir), args.path, args.branch, args.local, args.dry_run
            )
    except KeyboardInterrupt:
        print("aborted!")
        sys.exit(1)
    except subprocess.CalledProcessError as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)

# endregion
