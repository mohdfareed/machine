#!/usr/bin/env python3
"""
Machine Setup - Cross-platform dotfiles and environment manager.

Usage:
    ./setup.py <machine_id>              # Full setup
    ./setup.py <machine_id> --dry-run    # Preview changes
    ./setup.py <machine_id> --update     # Update packages/plugins
    ./setup.py --list                    # List available machines

Options:
    --private PATH    Path to private configs/keys (default: ~/.machine-private)
    --dry-run, -n     Preview changes without applying
    --debug, -d       Enable debug output

Bootstrap from scratch:
    curl -fsSL https://raw.githubusercontent.com/mohdfareed/machine/main/setup.py | python3 - macbook
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_URL = "https://github.com/mohdfareed/machine.git"
DEFAULT_PATH = Path.home() / ".machine"
DEFAULT_PRIVATE = Path.home() / ".machine-private"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "machine_id",
        nargs="?",
        help="Machine identifier (e.g., macbook, pc, rpi)",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List available machine configurations",
    )
    parser.add_argument(
        "--update",
        "-u",
        action="store_true",
        help="Update packages and plugins instead of install",
    )
    parser.add_argument(
        "--private",
        "-p",
        type=Path,
        default=DEFAULT_PRIVATE,
        help=f"Path to private configs/SSH keys (default: {DEFAULT_PRIVATE})",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Preview changes without applying",
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debug output",
    )
    parser.add_argument(
        "--packages-only",
        action="store_true",
        help="Only install packages",
    )
    parser.add_argument(
        "--dotfiles-only",
        action="store_true",
        help="Only setup dotfiles",
    )
    parser.add_argument(
        "--scripts-only",
        action="store_true",
        help="Only run scripts",
    )
    parser.add_argument(
        "--ssh-only",
        action="store_true",
        help="Only setup SSH keys",
    )

    args = parser.parse_args()

    # Ensure we're in the repo or clone it
    machine_root = ensure_repo()

    # Add to Python path
    sys.path.insert(0, str(machine_root))

    # Now import our modules (after path is set)
    from machine.core import (
        info,
        set_debug,
        set_dry_run,
    )
    from machine.dotfiles import setup_dotfiles
    from machine.packages import install_packages
    from machine.scripts import run_all_scripts
    from machine.ssh import setup_ssh
    from machine.update import update_all

    # Configure
    set_debug(args.debug)
    set_dry_run(args.dry_run)

    # List machines
    if args.list:
        return list_machines(machine_root)

    # Require machine_id for setup
    if not args.machine_id:
        parser.print_help()
        return 1

    machine_id = args.machine_id

    # Validate machine exists
    machine_dir = machine_root / "machines" / machine_id
    if not machine_dir.exists():
        print(f"error: unknown machine '{machine_id}'", file=sys.stderr)
        print(f"available: {', '.join(get_machine_ids(machine_root))}")
        return 1

    # Resolve private path
    private_path = args.private.expanduser() if args.private.exists() else None

    # Set environment variables for scripts
    os.environ["MACHINE"] = str(machine_root)
    os.environ["MACHINE_ID"] = machine_id
    os.environ["MACHINE_CONFIG"] = str(machine_dir)
    os.environ["MACHINE_SHARED"] = str(machine_root / "config")
    os.environ["MACHINE_PRIVATE"] = str(private_path or "")

    info(f"setting up machine: {machine_id}")

    # Handle update mode
    if args.update:
        update_all()
        info("update complete!")
        return 0

    # Run selected phases or all
    run_all = not (
        args.packages_only
        or args.dotfiles_only
        or args.scripts_only
        or args.ssh_only
    )

    if run_all or args.packages_only:
        install_packages(machine_id)

    if run_all or args.dotfiles_only:
        setup_dotfiles(machine_id, private_path)

    if run_all or args.ssh_only:
        setup_ssh(private_path)

    if run_all or args.scripts_only:
        run_all_scripts(machine_id)

    info("setup complete!")
    return 0


def ensure_repo() -> Path:
    """Ensure we have the repo, clone if needed."""
    # Check if we're already in the repo
    script_path = Path(__file__).resolve()
    if (
        script_path.parent.name == "machine"
        or (script_path.parent / "machine").is_dir()
    ):
        return script_path.parent

    # Check default location
    if DEFAULT_PATH.exists() and (DEFAULT_PATH / "machine").is_dir():
        return DEFAULT_PATH

    # Clone the repo
    print(f"cloning repository to {DEFAULT_PATH}...")
    subprocess.run(
        ["git", "clone", REPO_URL, str(DEFAULT_PATH)],
        check=True,
    )
    return DEFAULT_PATH


def get_machine_ids(root: Path) -> list[str]:
    """Get list of available machine IDs."""
    machines_dir = root / "machines"
    if not machines_dir.exists():
        return []
    return [
        d.name
        for d in machines_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ]


def list_machines(root: Path) -> int:
    """List available machine configurations."""
    machine_ids = get_machine_ids(root)
    if not machine_ids:
        print("no machines configured")
        return 1

    print("available machines:")
    for machine_id in sorted(machine_ids):
        print(f"  - {machine_id}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\naborted")
        sys.exit(130)
    except subprocess.CalledProcessError as e:
        print(
            f"error: command failed with exit code {e.returncode}",
            file=sys.stderr,
        )
        sys.exit(e.returncode)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
