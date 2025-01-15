#!/usr/bin/env python3
"""Script for setting up a local development environment."""

import argparse
import atexit
import os
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

# Configuration
REPOSITORY = "mohdfareed/machine.git"
REQUIRED_PATHS = [
    ".git",
    "pyproject.toml",
    ".pre-commit-config.yaml",
]

# Constants
PYTHON_VERSION = "3.9.6"


def main() -> None:
    """Set up the local development environment."""

    log_info("Setting up development environment...")

    _validate()
    _setup_python()
    poetry = _resolve_poetry()
    _setup_environment(poetry)
    _setup_pre_commit_hooks(poetry)

    log_success("Machine set up successfully")


# region: Setup


def _validate() -> None:
    atexit.register(lambda: os.chdir(os.getcwd()))
    os.chdir(Path(__file__).parent.parent)  # .py -> scripts -> machine
    for path in REQUIRED_PATHS:
        if not Path(path).exists():
            raise RuntimeError(f"Invalid repository: {path} not found")


def _setup_python() -> None:
    version_output = sys.version.split()[0]
    if version_output == PYTHON_VERSION:
        return

    log_warning(f"Python {version_output} is not supported.")
    if not shutil.which("pyenv"):
        err = f"Pyenv is required to install Python {PYTHON_VERSION}."
        raise RuntimeError(err)
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


# endregion

# region: Environment


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


# endregion

# region: Logging


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


class ScriptFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter,
):
    """Custom formatter for argparse help messages."""


def log_error(msg: str) -> None:
    """Log an error message."""
    print(f"\033[31m{'ERROR'}\033[0m    {msg}")


def log_success(msg: str) -> None:
    """Log a success message."""
    print(f"\033[35m{'SUCCESS'}\033[0m  {msg}")


def log_warning(msg: str) -> None:
    """Log a warning message."""
    print(f"\033[33m{'WARNING'}\033[0m  {msg}")


def log_info(msg: str) -> None:
    """Log an info message."""
    print(f"\033[34m{'INFO'}\033[0m     {msg}")


def panic(msg: str) -> None:
    """Log an error message and exit."""
    print(f"\033[31;1m{msg}\033[0m")
    sys.exit(1)


# endregion

# region: CLI

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=USAGE,
        formatter_class=ScriptFormatter,
    )
    args = parser.parse_args()

    try:  # Run script
        main()

    # Handle user interrupts
    except KeyboardInterrupt:
        print()
        log_warning("Aborted!")

    # Handle deployment errors
    except RuntimeError as e:
        log_error(f"{e}")
        panic("Failed to deploy machine")

    # Handle shell errors
    except subprocess.CalledProcessError as e:
        log_error(f"{e.returncode}: {' '.join(e.cmd)}")
        panic("An error occurred while running a shell command")

    # Handle unexpected errors
    except Exception as e:  # pylint: disable=broad-except
        print(f"Exception type: {type(e).__name__}")
        log_error(f"{e}")
        traceback.print_exc()
        panic("An unexpected error occurred")

# endregion
