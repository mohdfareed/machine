#!/usr/bin/env python3
"""
Set up a local development environment.

Creates a virtual environment with Poetry and installs the development
dependencies. Other development tools are also set up.

Requirements:
    - python 3.9.6
    - poetry

Note: The script must be run from the repository.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Union

# Configuration
REPOSITORY = "mohdfareed/machine.git"
PYTHON_VERSION = "3.9.6"  # default macos version

# Environment
ENV = os.environ.copy()
ENV["POETRY_VIRTUALENVS_IN_PROJECT"] = "true"


def main() -> None:
    """Set up the local development environment."""
    # Change to the repository root directory
    os.chdir(Path(__file__).parent.parent)  # .py -> scripts -> machine

    # Check if Poetry is installed
    if not shutil.which("poetry"):
        print("Error: Poetry not found.", file=sys.stderr)
        sys.exit(1)

    # Check if Python version is correct
    python = shutil.which("python3.9") or "python3.9" or sys.executable
    if python.split()[1] != PYTHON_VERSION:
        print(f"Error: Python {PYTHON_VERSION} is required.", file=sys.stderr)
        sys.exit(1)

    # Clean up existing virtual environment
    if Path(".venv").exists():
        print("Cleaning up existing...")
        shutil.rmtree(".venv")

    # Fetch updates from the repository
    print("Fetching changes...")
    run("git fetch --unshallow")
    run("git fetch --all --tags")

    # Install the application
    print("Installing app...")
    run(f"poetry env use {python}")
    run("poetry install -E dev")

    # Install pre-commit hooks
    print("Installing hooks...")
    run("poetry run pre-commit install --install-hooks")
    print("Environment setup complete.")


def run(cmd: Union[str, list[str]]) -> None:
    """Run a shell command."""
    cmd = cmd if isinstance(cmd, str) else " ".join(cmd)
    subprocess.run(cmd, shell=True, env=ENV, check=True)


# endregion

# region: CLI


class ScriptFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter,
): ...


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").strip(), formatter_class=ScriptFormatter
    )

    args = parser.parse_args()
    try:  # Run script
        main()

    # Handle user interrupts
    except KeyboardInterrupt:
        print("Aborted!")
        sys.exit(1)

    # Handle shell errors
    except subprocess.CalledProcessError as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


# endregion
