#!/usr/bin/env python3
"""Script for deploying a new machine."""

import argparse
import atexit
import os
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

# Configuration
DEFAULT_MACHINE_PATH = Path.home() / ".machine"
DEFAULT_BRANCH = "main"
REPOSITORY = "mohdfareed/machine.git"
EXECUTABLE = "machine-setup"

# Constants
POETRY_SCRIPT = "https://install.python-poetry.org"
POETRY_BUG_FIX = "sed 's/symlinks=False/symlinks=True/'"
if sys.platform == "win32":
    EXECUTABLE_PATH = Path.home() / "AppData" / "Local" / EXECUTABLE
else:
    EXECUTABLE_PATH = Path("/") / "usr" / "local" / "bin" / EXECUTABLE


def main(path: Path, branch: str) -> None:
    """Deploy a new machine."""

    log_info(f"Deploying machine to: {path}")
    _validate(path)
    _clone_app(path, branch)
    poetry = _install_poetry(path)
    _install_machine(path, poetry)
    log_success("Machine deployed successfully")


# region: Repository


def _validate(path: Path) -> None:
    cwd = os.getcwd()
    atexit.register(lambda: os.chdir(cwd))

    path.parent.mkdir(parents=True, exist_ok=True)
    if not os.access(path.parent, os.W_OK):
        raise RuntimeError(f"Permission denied: {path.parent}")

    if not shutil.which("git"):
        raise RuntimeError("Git is not installed")
    if not shutil.which("wget") and sys.platform == "win32":
        raise RuntimeError("Wget is not installed")
    if not shutil.which("curl") and sys.platform != "win32":
        raise RuntimeError("Curl is not installed")


def _clone_app(path: Path, branch: str) -> None:
    if path.exists():
        log_warning("Machine app already exists")
        return

    log_info(f"Cloning machine app branch: {branch}")
    url = f"https://github.com/{REPOSITORY}"
    subprocess.run(
        f"git clone -b {branch} {url} {path} --depth 1",
        check=True,
        shell=True,
    )
    os.chdir(path)  # machine


# endregion

# region: Poetry


def _install_poetry(path: Path) -> Path:
    if poetry := shutil.which("poetry"):
        return Path(poetry)
    log_warning("Poetry not found")
    log_info("Installing poetry...")
    poetry_path = path / ".poetry"

    if os.name != "nt":
        _install_poetry_unix(poetry_path)
    else:  # Windows
        _install_poetry_windows(poetry_path)
    log_success("Poetry installed successfully")
    return poetry_path / "bin" / "poetry"


def _install_poetry_unix(path: Path) -> None:
    cmd = f"curl -sSL {POETRY_SCRIPT}"
    subprocess.run(
        f"{cmd} | {POETRY_BUG_FIX} | python3 -",
        env={"POETRY_HOME": path},
        check=True,
        shell=True,
    )


def _install_poetry_windows(path: Path) -> None:
    cmd = f"(wget -Uri {POETRY_SCRIPT} -UseBasicParsing).Content"
    subprocess.run(
        f"{cmd} | {POETRY_BUG_FIX} | py -",
        env={"POETRY_HOME": path},
        check=True,
        executable="powershell",
        shell=True,
    )


# endregion

# region: Executable


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
        cmd = "New-Item -ItemType Directory -Force -Path"
        subprocess.run(
            f"{cmd} {EXECUTABLE_PATH.parent} -ErrorAction SilentlyContinue",
            check=True,
            executable="powershell",
            shell=True,
        )
        cmd = "New-Item -ItemType SymbolicLink -Force -Path"
        subprocess.run(
            f"{cmd} {EXECUTABLE_PATH.parent} -Target {machine_setup}",
            check=True,
            executable="powershell",
            shell=True,
        )


# endregion

# region: Logging

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

    # Parse arguments
    args = parser.parse_args()
    machine_path: Path = args.path
    branch_name: str = args.branch

    try:  # deploy machine
        main(machine_path, branch_name)

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
