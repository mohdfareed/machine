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
CHEZMOI = f'sh -c "$(curl -fsLS get.chezmoi.io)" --'


def main(path: Path, local: bool, bin: Path, args: list[str]) -> None:
    """Install application."""
    path = path.expanduser().resolve()
    bin = bin.expanduser().resolve()
    options = " ".join(args).strip()

    repo = f"git@github.com:{REPOSITORY}.git" if not local else ""
    chezmoi = f"{CHEZMOI} -b {bin}"
    if shutil.which("chezmoi"):
        chezmoi = "chezmoi"

    print(f"bootstrapping machine at: {path}")
    run(f"{chezmoi} init --apply --source {path} {repo} {options}")
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
        default=Path.home() / ".machine",
    )
    parser.add_argument("--local", action="store_true", help="use local repo")
    args, extra = parser.parse_known_args()

    try:  # Run script
        with TemporaryDirectory() as tempdir:
            main(args.path, args.local, Path(tempdir), extra)
    except KeyboardInterrupt:
        print("aborted!")
        sys.exit(1)
    except subprocess.CalledProcessError as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)

# endregion
