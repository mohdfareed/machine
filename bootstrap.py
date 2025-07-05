#!/usr/bin/env python3
"""
Deploy a new machine by installing the machine setup app.

Clones the machine repository and installs the application using Poetry.
If Poetry is not installed, it is installed locally first. The executable is
symlinked to the pip installation path.

Requirements:
    - git
    - pip

For macOS, Command Line Tools for Xcode is required. Install it using:
xcode-select --install
"""

# FIXME: Deploy using Chezmoi

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Union

# Configuration
DEFAULT_MACHINE_PATH = Path.home() / ".machine"
REPOSITORY = "mohdfareed/machine"
EXECUTABLE = "machine"

# Constants
POETRY_SCRIPT = "https://install.python-poetry.org"
POETRY_BUG_FIX = "sed 's/symlinks=False/symlinks=True/'"

# Environment
ENV = os.environ.copy()


def main(path: Path) -> None:
    """Install application."""
    poetry_home = path / ".poetry"
    ENV["POETRY_HOME"] = str(poetry_home)

    if sys.platform == "win32":
        executable = poetry_home / "Scripts" / f"{EXECUTABLE}.exe"
    else:  # Unix-based
        executable = poetry_home / "bin" / EXECUTABLE

    # resolve installation path
    pip_info = run("pip show pip").stdout.decode()
    location_match = re.search(r"^Location:\s*(.*)$", pip_info, re.MULTILINE)
    bin = location_match.group(1) if location_match else None
    if not bin or not bin.strip():
        raise RuntimeError(
            "Failed to find pip installation location.", pip_info
        )
    executable_path = (Path(bin.strip()) / EXECUTABLE).with_suffix(
        ".exe" if sys.platform == "win32" else ""
    )

    if not shutil.which("git"):
        print("Error: Git is not installed.", file=sys.stderr)
        sys.exit(1)
    path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Deploying machine to: {path}")
    repo = f"https://github.com/{REPOSITORY}.git"
    run(f"git clone {repo} {path} --depth 1")
    os.chdir(path)  # machine

    if not (poetry := shutil.which("poetry")):
        print("Installing poetry...")
        if os.name != "nt":
            run(f"curl -sSL {POETRY_SCRIPT} | {POETRY_BUG_FIX} | python3 -")
        else:  # Windows
            cmd = f"(wget -Uri {POETRY_SCRIPT} -UseBasicParsing).Content"
            run(f"{cmd} | {POETRY_BUG_FIX} | py -")
        poetry = poetry_home / "bin" / "poetry"

    print("Installing application...")
    run(f"{poetry} install")
    executable_path.symlink_to(executable)

    print(f"Linked executable: {executable_path} -> {executable}")
    print("Machine deployed successfully.")


def run(cmd: Union[str, list[str]]) -> subprocess.CompletedProcess[bytes]:
    cmd = cmd if isinstance(cmd, str) else " ".join(cmd)
    return subprocess.run(cmd, shell=True, env=ENV, check=True)


# region: CLI

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=(__doc__ or "").strip())
    parser.add_argument(
        "-p",
        "--path",
        type=Path,
        help="machine installation path",
        default=DEFAULT_MACHINE_PATH,
    )

    args = parser.parse_args()
    try:  # Run script
        main(args.path)

    # Handle exceptions
    except KeyboardInterrupt:
        print("Aborted!")
        sys.exit(1)
    except subprocess.CalledProcessError as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

# endregion
