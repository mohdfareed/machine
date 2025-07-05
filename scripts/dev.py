#!/usr/bin/env python3
"""
Set up a local development environment.

Creates a virtual environment with UV and installs the development
dependencies. Other development tools are also set up.

Requirements:
    - git
    - uv

Note: The script must be run from the repository.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Union

# Configuration
REPOSITORY = "mohdfareed/machine.git"
PYTHON_VERSION = "3.9.6"  # default macos version

# Environment
VENV = Path(".venv")
ENV = os.environ.copy()


def main() -> None:
    """Set up the local development environment."""
    # Change to the repository root directory
    os.chdir(Path(__file__).parent.parent)  # .py -> scripts -> machine

    # Fetch updates from the repository
    print("Fetching changes...")
    if (Path(".git") / "shallow").exists():
        run("git fetch --unshallow")
    run("git fetch --all --tags --prune")

    # Install the application
    print("Installing app...")
    run(f"uv python install {PYTHON_VERSION}")
    run(f"uv venv {VENV} --python {PYTHON_VERSION}")
    run("uv sync --extra dev")

    # Install pre-commit hooks
    print("Installing hooks...")
    run("uv run pre-commit install --install-hooks")
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
