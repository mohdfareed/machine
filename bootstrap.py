#!/usr/bin/env python3
"""
Deploy a new machine using Chezmoi.

Installs Chezmoi and bootstraps a new machine at a path.

Requirements:
    - Python 3.8 or later
    - Chezmoi (installed via the script if unavailable)
    - PowerShell 7.0 or later (Windows)
    - Xcode Command Line Tools (macOS)

Install XCode Command Line Tools on macOS:
xcode-select --install

Chezmoi installation docs:
https://www.chezmoi.io/install/#one-line-binary-install
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

REPOSITORY = "mohdfareed/machine"
DEFAULT_MACHINE = (
    os.environ.get("MACHINE") or Path("~/.machine").expanduser().resolve()
)

INSTALL_CHEZMOI = 'sh -c "$(curl -fsLS get.chezmoi.io)" -- -b "{}"'
INSTALL_CHEZMOI_WIN = "&{$(irm 'https://get.chezmoi.io/ps1')} -b '{}'"
IS_WINDOWS = sys.platform.lower().startswith("win32")


def main(path: Path, bin: Path, args: "list[str]") -> None:
    """Install application."""
    path = path.expanduser().resolve()
    options = " ".join(args).strip()

    chezmoi = "chezmoi"
    if not shutil.which(chezmoi):
        chezmoi = install_chezmoi(bin)

    print(f"bootstrapping machine at: {path}")
    run(f"{chezmoi} init --apply --source {path} {REPOSITORY} {options}")
    print("machine bootstrapped successfully")


def install_chezmoi(bin: Path) -> str:
    """Install Chezmoi binary and return executable path."""
    bin = bin.expanduser().resolve()
    bin.mkdir(parents=True, exist_ok=True)
    print("installing chezmoi...")

    if IS_WINDOWS:
        run(f'iex "{INSTALL_CHEZMOI_WIN.format(bin)}"')
        return str(bin / "chezmoi.exe")
    else:  # unix
        run(INSTALL_CHEZMOI.format(bin))
        return str(bin / "chezmoi")


def run(cmd: str) -> subprocess.CompletedProcess[bytes]:
    exe = shutil.which("powershell.exe") if IS_WINDOWS else None
    return subprocess.run(cmd.strip(), shell=True, check=True, executable=exe)


# region: CLI

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # machine setup path
    parser.add_argument(
        "path",
        type=Path,
        help="machine path",
        default=DEFAULT_MACHINE,
        nargs="?",
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
        with TemporaryDirectory() as temp:  # temp bin for chezmoi
            main(args.path, Path(temp), extra)
        print("done!")
        sys.exit(0)

    except KeyboardInterrupt:
        print("aborted!")
        sys.exit(1)

    except subprocess.CalledProcessError as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)

# endregion
