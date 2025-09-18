#!/usr/bin/env python3
"""
Machine setup CLI tool.
"""

import argparse
import enum
import os
import subprocess
import sys
from pathlib import Path

import utils


class ScriptCommand(enum.StrEnum):
    SCRIPTS = "scripts"
    PACKAGES = "packages"
    SSH = "ssh"


def main(command: ScriptCommand | None, args: list[str]) -> None:
    utils.debug("cli", f"command: {command}")
    utils.debug("cli", f"args: {args}")
    machine = Path(utils.get_env("MACHINE")).expanduser()

    if command is None and not args:
        chezmoi_apply(machine)
        return
    if command is None:  # args only
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


def chezmoi_command(args: list[str]) -> None:
    print(f"running: chezmoi {' '.join(args)}...")
    utils.run(f"chezmoi {' '.join(args)}")


def run_script(command: ScriptCommand, args: list[str]) -> None:
    script_path = Path(__file__).parent / f"{command.value}.py"
    argv = " ".join(arg for arg in args)
    utils.debug("cli", f"running: {script_path} {argv}...")
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
        "args", nargs="*", help="arguments to pass to the command"
    )
    args = parser.parse_args()

    try:  # validate command
        args.cmd = ScriptCommand(args.cmd)
    except ValueError:
        args.args = [args.cmd] + args.args if args.cmd else args.args
        args.cmd = None  # treat as chezmoi command if invalid

    if args.debug:
        os.environ["DEBUG"] = "1"
    if args.dry_run:
        os.environ["DRY_RUN"] = "1"
    utils.script_entrypoint("cli", lambda: main(args.cmd, args.args))

# endregion
