#!/usr/bin/env python3
"""Script for deploying a new machine."""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from scripts.helpers import *  # pylint: disable=wildcard-import,unused-wildcard-import

# Configuration
DEFAULT_MACHINE_PATH = Path.home() / ".machine"
EXECUTABLE = "machine-setup"

# Help message
USAGE = """
Deploy a new machine by installing the machine setup app.

Installs the machine app using poetry and links the executable to the
local bin directory.

Installs poetry if not found. It is installed using the official script.
The script is found at: https://install.python-poetry.org

Requirements:
    - git
    - curl (for Unix)

For macOS, Command Line Tools for Xcode is required. Install it using:
xcode-select --install
""".strip()

# Constants
if sys.platform == "win32":
    EXECUTABLE_PATH = Path.home() / "AppData" / "Local" / EXECUTABLE
else:
    EXECUTABLE_PATH = Path("/") / "usr" / "local" / "bin" / EXECUTABLE


def main(path: Path) -> None:
    """Deploy a new machine."""

    log_info(f"Deploying machine to: {path}")

    _validate(path)
    _clone_app(path)
    poetry = _install_poetry(path)
    _install_machine(path, poetry)

    log_success("Machine deployed successfully")


def _validate(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not os.access(path.parent, os.W_OK):
        raise RuntimeError(f"Permission denied: {path.parent}")

    if not shutil.which("git"):
        raise RuntimeError("Git is not installed")
    if not shutil.which("wget") and sys.platform == "win32":
        raise RuntimeError("Wget is not installed")
    if not shutil.which("curl") and sys.platform != "win32":
        raise RuntimeError("Curl is not installed")


def _clone_app(path: Path) -> None:
    if path.exists():
        log_warning("Machine app already exists")
        return

    log_info("Cloning machine app...")
    subprocess.run(
        [
            "git",
            "clone",
            f"https://github.com/{REPOSITORY}",
            path,
            "--depth",
            "1",
        ],
        check=True,
    )


def _install_poetry(path: Path) -> Path:
    if poetry := shutil.which("poetry"):
        return Path(poetry)

    log_warning("Poetry not found")
    log_info("Installing poetry...")
    poetry_path = path / ".poetry"

    # Windows
    if os.name == "nt":
        _install_poetry_windows(poetry_path)
    # Unix
    else:
        _install_poetry_unix(poetry_path)

    log_success("Poetry installed successfully")
    return poetry_path / "bin" / "poetry"


def _install_poetry_unix(path: Path) -> None:
    subprocess.run(
        " ".join(
            [
                "curl",
                "-sSL",
                "https://install.python-poetry.org",
                "|",
                "python3",
                "-",
            ]
        ),
        env={"POETRY_HOME": path},
        check=True,
        shell=True,
    )


def _install_poetry_windows(path: Path) -> None:
    subprocess.run(
        " ".join(
            [
                "(wget -Uri https://install.python-poetry.org "
                "-UseBasicParsing).Content",
                "|",
                "py",
                "-",
            ]
        ),
        env={"POETRY_HOME": path},
        check=True,
        executable="powershell",
        shell=True,
    )


def _install_machine(path: Path, poetry: Path) -> None:
    log_info("Installing machine...")
    subprocess.run(
        [poetry, "install"],
        env={"POETRY_VIRTUALENVS_IN_PROJECT": "true"},
        cwd=path,
        check=True,
    )
    _link_executable(path)


def _link_executable(path: Path) -> None:
    log_info(f"Linking executable to: {EXECUTABLE_PATH}")
    machine_setup = path / ".venv" / "bin" / EXECUTABLE

    if sys.platform != "win32":
        subprocess.run(
            ["sudo", "mkdir", "-p", EXECUTABLE_PATH.parent],
            check=True,
        )
        subprocess.run(
            ["sudo", "ln", "-sf", machine_setup, EXECUTABLE_PATH],
            check=True,
        )
    else:  # Windows
        subprocess.run(
            [
                "New-Item",
                "-ItemType",
                "Directory",
                "-Force",
                "-Path",
                EXECUTABLE_PATH.parent,
                "-ErrorAction",
                "SilentlyContinue",
            ],
            check=True,
            executable="powershell",
        )
        subprocess.run(
            [
                "New-Item",
                "-ItemType",
                "SymbolicLink",
                "-Force",
                "-Path",
                EXECUTABLE_PATH,
                "-Target",
                machine_setup,
            ],
            check=True,
            executable="powershell",
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=USAGE,
        formatter_class=ScriptFormatter,
    )

    # Add arguments
    parser.add_argument(
        "machine_path",
        type=Path,
        help="machine installation path",
        nargs="?",
        default=DEFAULT_MACHINE_PATH,
    )

    # Parse arguments
    args = parser.parse_args()
    machine_path: Path = args.machine_path

    # deploy machine
    run_main(lambda: main(machine_path))
