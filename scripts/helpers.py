"""Scripts helper functions."""

__all__ = [
    "REPOSITORY",
    "ScriptFormatter",
    "run_main",
    "log_error",
    "log_info",
    "log_success",
    "log_warning",
    "panic",
]

import argparse
import atexit
import os
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Callable

# Set the current working directory to the machine directory.
# Restore the original working directory when the script exits.
atexit.register(lambda: os.chdir(os.getcwd()))
os.chdir(Path(__file__).parent.parent)  # .py -> scripts -> machine

REPOSITORY = "mohdfareed/machine.git"


class ScriptFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter,
):
    """Custom formatter for argparse help messages."""


def run_main(main: Callable[[], None]) -> None:
    """Run the main function and catch exceptions."""
    try:
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
