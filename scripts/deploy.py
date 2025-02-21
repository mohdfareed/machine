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
DEFAULT_BRANCH = "main"
REPOSITORY = "mohdfareed/machine"
EXECUTABLE = "machine-setup"

# Constants
POETRY_SCRIPT = "https://install.python-poetry.org"
POETRY_BUG_FIX = "sed 's/symlinks=False/symlinks=True/'"
ENV = os.environ.copy()


def main(path: Path, branch: str, dev: bool) -> None:
    """Install application."""
    ENV["POETRY_HOME"] = str(path / ".poetry")
    ENV["POETRY_VIRTUALENVS_IN_PROJECT"] = "true"
    if sys.platform == "win32":
        executable = path / "Scripts" / f"{EXECUTABLE}.exe"
    else:  # Unix-based
        executable = path / "bin" / EXECUTABLE

    # resolve installation path
    pip_info = run("pip show pip").stdout.decode()
    location_match = re.search(r"^Location:\s*(.*)$", pip_info, re.MULTILINE)
    bin = location_match.group(1) if location_match else None
    if not bin or not bin.strip():
        raise RuntimeError(
            "Failed to find pip installation location.", pip_info
        )
    executable_path = Path(bin.strip()) / executable

    if not shutil.which("git"):
        print("Error: Git is not installed.", file=sys.stderr)
        sys.exit(1)
    path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Deploying machine to: {path}")
    repo = f"https://github.com/{REPOSITORY}.git"
    run(f"git clone -b {branch} {repo} {path} --depth 1")
    os.chdir(path)  # machine

    if not (poetry := shutil.which("poetry")):
        print("Installing poetry...")
        if os.name != "nt":
            run(f"curl -sSL {POETRY_SCRIPT} | {POETRY_BUG_FIX} | python3 -")
        else:  # Windows
            cmd = f"(wget -Uri {POETRY_SCRIPT} -UseBasicParsing).Content"
            run(f"{cmd} | {POETRY_BUG_FIX} | py -")
        poetry = Path(ENV["POETRY_HOME"]) / "bin" / "poetry"

    print("Installing application...")
    run(f"{poetry} install " + "-E dev" if dev else "")
    executable_path.symlink_to(executable)
    print(f"Linked executable: {executable_path} -> {executable}")
    print("Machine deployed successfully.")


def run(cmd: Union[str, list[str]]) -> subprocess.CompletedProcess[bytes]:
    cmd = cmd if isinstance(cmd, str) else " ".join(cmd)
    return subprocess.run(cmd, shell=True, env=ENV, check=True)


# region: CLI


class ScriptFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter,
): ...


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").strip(), formatter_class=ScriptFormatter
    )

    # Add arguments
    parser.add_argument(
        "-p",
        "--path",
        type=Path,
        help="machine installation path",
        default=DEFAULT_MACHINE_PATH,
    )
    parser.add_argument(
        "branch",
        type=Path,
        help="machine repository branch",
        nargs="?",
        default=DEFAULT_BRANCH,
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="install in development mode",
    )

    # Parse arguments
    args = parser.parse_args()
    try:  # Install the application
        main(args.path, args.branch, args.dev)

    # Handle user interrupts
    except KeyboardInterrupt:
        print("Aborted!")
        sys.exit(1)

    # Handle shell errors
    except subprocess.CalledProcessError as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


# endregion
