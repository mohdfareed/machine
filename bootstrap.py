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
Chezmoi installation:
https://www.chezmoi.io/install/#one-line-binary-install
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

REPOSITORY = "mohdfareed/machine"
CHEZMOI = 'sh -c "$(curl -fsLS get.chezmoi.io)" --'
CHEZMOI_WIN = 'winget install twpayne.chezmoi'

DEFAULT_MACHINE = Path("~/.machine").expanduser().resolve()
WINDOWS = sys.platform.lower().startswith("win32")

def main(path: Path, local: bool, bin: Path, args: list[str]) -> None:
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
    """Install Chezmoi binary."""
    bin = bin.expanduser().resolve()
    bin.mkdir(parents=True, exist_ok=True)

    print(f"installing chezmoi...")
    if WINDOWS:
        run(CHEZMOI_WIN)
    else: # windows
        run(f"{CHEZMOI} -b {bin}")
    return str(bin / "chezmoi.exe" if WINDOWS else "chezmoi")


def run(cmd: str) -> subprocess.CompletedProcess[bytes]:
    exe = shutil.which("powershell.exe") if WINDOWS else None
    return subprocess.run(cmd.strip(), shell=True, check=True, executable=exe)


# region: CLI

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "path", type=Path, help="machine path", default=DEFAULT_MACHINE,
    )
    parser.add_argument("--local", action="store_true", help="use local repo")
    args, extra = parser.parse_known_args()

    try:  # run script
        with TemporaryDirectory() as temp:  # temp bin for chezmoi
            main(args.path, args.local, Path(temp), extra)
    except KeyboardInterrupt:
        print("aborted!")
        sys.exit(1)
    except subprocess.CalledProcessError as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)

# endregion
