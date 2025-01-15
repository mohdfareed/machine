#!/usr/bin/env python3
"""Script for setting up a local development environment."""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from scripts.helpers import *  # pylint: disable=wildcard-import,unused-wildcard-import

# Help message
USAGE = """
Set up a local development environment.

Creates a virtual environment with Poetry and installs the development
dependencies. Other development tools are also set up.
The script must be run in the repository.

Requirements:
    - python 3.9.6 or pyenv
    - poetry or pipx

If Poetry is not installed, pipx is used to install it.
If Python 3.9.6 is not installed, pyenv is used to install it.
""".strip()

# Constants
PYTHON_VERSION = "3.9.6"


def main() -> None:
    """Main function to set up the local development environment."""

    log_info("Setting up development environment...")

    _validate()
    _setup_python()
    poetry = _resolve_poetry()
    _setup_environment(poetry)
    _setup_pre_commit_hooks(poetry)

    log_success("Machine set up successfully")


def _validate() -> None:
    if not Path("pyproject.toml").exists():
        raise RuntimeError("This script must be run from the repository.")


def _setup_python() -> None:
    version_output = sys.version.split()[0]
    if version_output == PYTHON_VERSION:
        return

    log_warning(f"Python {version_output} is not supported.")
    if not shutil.which("pyenv"):
        raise RuntimeError(f"Pyenv is required to install Python {PYTHON_VERSION}.")
    _install_python()


def _resolve_poetry() -> Path:
    if poetry := shutil.which("poetry"):
        return Path(poetry)

    log_warning("Poetry is not installed")
    if not shutil.which("pipx"):
        raise RuntimeError("Pipx is required to install Poetry.")
    return _install_poetry()


def _install_python() -> None:
    log_info(f"Installing Python {PYTHON_VERSION}...")
    subprocess.run(["pyenv", "install", PYTHON_VERSION], check=False)
    subprocess.run(["pyenv", "local", PYTHON_VERSION], check=True)
    log_success(f"Python {PYTHON_VERSION} installed via pyenv.")


def _install_poetry() -> Path:
    log_info("Installing Poetry with pipx...")
    subprocess.run(["pipx", "install", "poetry"], check=True)
    log_success("Poetry installed successfully")
    log_warning("Restart the shell to update the PATH")
    sys.exit()


def _setup_environment(poetry: Path) -> None:
    log_info("Installing development dependencies with Poetry...")
    subprocess.run(
        [poetry, "env", "use", shutil.which("python3.9") or "python3.9"],
        env={"POETRY_VIRTUALENVS_IN_PROJECT": "true"},
        check=True,
    )
    subprocess.run(
        [poetry, "install", "--with", "dev"],
        env={"POETRY_VIRTUALENVS_IN_PROJECT": "true"},
        check=True,
    )


def _setup_pre_commit_hooks(poetry: Path) -> None:
    log_info("Setting up pre-commit hooks...")
    subprocess.run(
        [poetry, "run", "pre-commit", "install", "--install-hooks"],
        check=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=USAGE,
        formatter_class=ScriptFormatter,
    )
    args = parser.parse_args()
    run_main(main)
