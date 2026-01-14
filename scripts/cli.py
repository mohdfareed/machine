#!/usr/bin/env python3
"""Machine setup CLI tool."""

import argparse
import enum
import os
import subprocess
import sys
from pathlib import Path
from typing import Union

import utils


class ScriptCommand(enum.Enum):
    CHEZMOI = "chezmoi"
    UPDATE = "update"
    SCRIPTS = "scripts"
    PACKAGES = "packages"
    SSH = "ssh"


def main(command: Union[ScriptCommand, None], args: "list[str]") -> None:
    machine = Path(utils.get_env("MACHINE", str)).expanduser()

    if command is None and not args:
        chezmoi_apply(machine)
        return
    if command is None or command is ScriptCommand.CHEZMOI:
        chezmoi_command(args)
        return
    run_script(command, args)


def chezmoi_apply(machine: Path) -> None:
    try:
        print("updating machine...")
        utils.run("git pull")
    except subprocess.CalledProcessError:
        utils.debug("cli", "git pull failed, continuing...")

    print("applying machine config...")
    utils.run(f'chezmoi init --apply --source "{str(machine)}"')


def chezmoi_command(args: "list[str]") -> None:
    utils.run(f"chezmoi {' '.join(args)}")


def run_script(command: ScriptCommand, args: "list[str]") -> None:
    script_path = Path(__file__).parent / f"{command.value}.py"
    argv = " ".join(arg for arg in args)
    subprocess.run(
        f'{sys.executable} "{script_path}" {argv}',
        shell=True,
        check=True,
    )


# region: CLI

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )

    parser.add_argument(
        "--help",
        "-h",
        action="store_true",
        help="show this help message and exit",
    )
    parser.add_argument(
        "--debug", "-d", action="store_true", help="print debug information"
    )
    parser.add_argument(
        "--dry-run", "-n", action="store_true", help="perform a dry run"
    )
    parser.add_argument(
        "cmd",
        nargs="?",
        help=f"command to run ({', '.join(c.value for c in ScriptCommand)})",
    )
    parser.add_argument(
        "args", nargs="*", help="arguments for the command (if any)"
    )

    # parse arguments
    args, unknown_args = parser.parse_known_args()
    args.args += unknown_args
    try:  # validate command
        args.cmd = ScriptCommand(args.cmd)
    except ValueError:
        args.args = [args.cmd] + args.args if args.cmd else args.args
        args.cmd = None  # treat as chezmoi command if invalid

    # print help if no command and no args
    if args.help and args.cmd is None and not args.args:
        parser.print_help()
        sys.exit(0)
    if args.help:  # print help for subcommand
        args.args = args.args + ["--help"]

    # set environment variables and run
    os.environ["DEBUG"] = "1" if args.debug else ""
    os.environ["DRY_RUN"] = "1" if args.dry_run else ""
    utils.script_entrypoint("cli", lambda: main(args.cmd, args.args))

# endregion
