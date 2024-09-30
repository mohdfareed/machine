#!/usr/bin/env python3
"""Script for setting up a local development environment."""

import argparse
import os
import shutil
import subprocess
import sys

PYTHON_VERSION = "3.9.6"


def _log_error(msg: str):
    print(f"\033[31m{'ERROR'}\033[0m    {msg}")


def _log_success(msg: str):
    print(f"\033[35m{'SUCCESS'}\033[0m  {msg}")


def _log_info(msg: str):
    print(f"\033[34m{'INFO'}\033[0m     {msg}")


def _log_warning(msg: str):
    print(f"\033[33m{'WARNING'}\033[0m  {msg}")


def _validate_env():
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if os.path.exists("pyproject.toml"):
        return

    _log_error("This script must be run from the repository.")
    sys.exit(1)


def _validate_python():
    version_output = sys.version.split()[0]
    if version_output == PYTHON_VERSION:
        return

    _log_warning(f"Python {version_output} is not supported.")
    if not shutil.which("pyenv"):
        _log_error(f"Pyenv is required to install Python {PYTHON_VERSION}.")
        sys.exit(1)

    _log_info(f"Installing Python {PYTHON_VERSION}...")
    subprocess.run(["pyenv", "install", PYTHON_VERSION], check=False)
    subprocess.run(["pyenv", "local", PYTHON_VERSION], check=True)
    _log_success(f"Python {PYTHON_VERSION} installed via pyenv.")


def _resolve_poetry() -> str:
    if poetry := shutil.which("poetry"):
        return poetry

    _log_warning("Poetry is not installed.")
    if not shutil.which("pipx"):
        _log_error("Pipx is required to install Poetry.")
        sys.exit(1)

    _log_info("Installing Poetry with pipx...")
    subprocess.run(["pipx", "install", "poetry"], check=True)
    _log_success("Poetry installed successfully.")
    if poetry := shutil.which("poetry"):
        return poetry

    _log_error("Poetry is not available in the PATH.")
    _log_warning("Restart the shell to update the PATH.")
    sys.exit(1)


def _setup_environment(poetry: str):
    _log_info("Installing development dependencies with Poetry...")
    subprocess.run(
        [poetry, "install", "--with", "dev"],
        env={"POETRY_VIRTUALENVS_IN_PROJECT": "true"},
        check=True,
    )

    _log_info("Setting up pre-commit hooks...")
    subprocess.run(
        ["poetry", "run", "pre-commit", "install", "--install-hooks"],
        check=True,
    )


def main():
    """Main function to set up the local development environment."""
    _log_info("Setting up development environment...")

    _validate_env()
    _validate_python()
    poetry = _resolve_poetry()
    _setup_environment(poetry)

    _log_success("Development environment set up successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""
        Set up a local development environment.

        The script must be run within the repository.
        If Python 3.9.6 is not installed, pyenv is used to install it.
        if Poetry is not installed, the script will install it with pipx.

        Requirements: python 3.9.6 or pyenv, poetry or pipx.
        """,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    args = parser.parse_args()

    try:
        main()
    except KeyboardInterrupt:
        _log_warning("Aborted.")
        sys.exit(1)
    except Exception as e:  # pylint: disable=broad-except
        _log_error(f"Setup failed: {e}")
        sys.exit(1)
