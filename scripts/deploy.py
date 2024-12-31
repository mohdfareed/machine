#!/usr/bin/env python3
"""Script for deploying a new machine."""

import argparse
import os
import shutil
import subprocess
import sys

_home = os.environ.get("HOME", os.path.expanduser("~"))
DEFAULT_MACHINE_PATH = os.path.join(_home, ".machine")

APP_URL = "https://github.com/mohdfareed/machine.git"
EXECUTABLE = "machine-setup"

if os.name == "nt":
    EXECUTABLE_PATH = os.path.join(_home, "AppData", "Local", EXECUTABLE)
else:
    EXECUTABLE_PATH = os.path.join(
        os.environ.get("XDG_LOCAL_HOME", os.path.expanduser("~/.local")),
        "bin",
        EXECUTABLE,
    )


def main(path: str) -> None:
    """Deploy a new machine."""
    _log_info(f"Deploying machine to: {path}")

    _validate_git()
    _clone_app(path)
    poetry = _install_poetry(path)
    _install_machine(path, poetry)
    _link_executable(path)

    _log_success("Machine deployed successfully")


def _validate_git() -> None:
    if shutil.which("git"):
        return

    _log_error("git is required")
    sys.exit(1)


def _clone_app(path: str) -> None:
    if os.path.exists(path):
        return

    _log_info("Cloning machine app...")
    subprocess.run(
        ["git", "clone", APP_URL, path, "--depth", "1"],
        check=True,
    )


def _install_poetry(path: str) -> str:
    if poetry := shutil.which("poetry"):
        return poetry

    _log_info("Installing poetry...")
    poetry_path = os.path.join(path, ".poetry")

    # Windows
    if os.name == "nt":
        subprocess.run(
            [
                "(Invoke-WebRequest -Uri https://install.python-poetry.org "
                "-UseBasicParsing).Content",
                "|",
                "py",
                "-",
            ],
            env={"POETRY_HOME": poetry_path},
            check=True,
            executable="powershell",
        )

    # Unix
    else:
        subprocess.run(
            [
                "curl",
                "-sSL",
                "https://install.python-poetry.org",
                "|",
                "python3",
                "-",
            ],
            env={"POETRY_HOME": poetry_path},
            check=True,
        )

    _log_success("Poetry installed successfully")
    return os.path.join(poetry_path, "bin", "poetry")


def _install_machine(path: str, poetry: str) -> None:
    _log_info("Installing machine...")
    subprocess.run(
        [poetry, "env", "use", "3.9.6"],
        env={"POETRY_VIRTUALENVS_IN_PROJECT": "true"},
        cwd=path,
        check=True,
    )
    subprocess.run(
        [poetry, "install"],
        env={"POETRY_VIRTUALENVS_IN_PROJECT": "true"},
        cwd=path,
        check=True,
    )


def _link_executable(path: str) -> None:
    machine_setup = os.path.join(path, ".venv", "bin", EXECUTABLE)
    if os.path.islink(EXECUTABLE_PATH) or os.path.exists(EXECUTABLE_PATH):
        os.remove(EXECUTABLE_PATH)
    _log_info(f"Linking executable to: {EXECUTABLE_PATH}")
    os.symlink(machine_setup, EXECUTABLE_PATH)


def _log_error(msg: str) -> None:
    print(f"\033[31m{'ERROR'}\033[0m    {msg}")


def _log_success(msg: str) -> None:
    print(f"\033[35m{'SUCCESS'}\033[0m  {msg}")


def _log_warning(msg: str) -> None:
    print(f"\033[33m{'WARNING'}\033[0m  {msg}")


def _log_info(msg: str) -> None:
    print(f"\033[34m{'INFO'}\033[0m     {msg}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""
        Deploy a new machine by installing the machine app.

        Installs the machine app using poetry and links the executable to the
        local bin directory.

        Installs poetry if not found. It is installed using pipx if available,
        else it is installed using the official script.

        Requirements: git.
        """,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "machine_path",
        type=str,
        help="machine installation path",
        nargs="?",
        default=DEFAULT_MACHINE_PATH,
    )

    # Parse arguments
    args = parser.parse_args()
    machine_path = args.machine_path

    try:
        main(machine_path)
    except KeyboardInterrupt:
        _log_warning("Aborted!")
        sys.exit(0)
    except Exception as e:  # pylint: disable=broad-except
        _log_error(f"{e}")
        print(f"\033[31;1m{'Failed to deploy machine.'}\033[0m")
        sys.exit(1)
