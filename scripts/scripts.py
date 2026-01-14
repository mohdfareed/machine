#!/usr/bin/env python3
"""
Cross-platform script runner.

Reads JSON from CHEZMOI_DATA and runs scripts using the appropriate shell.
If CHEZMOI_DATA is not set, falls back to finding scripts in the machine
config directories.
Respects DEBUG and DRY_RUN environment variables.

Expected JSON structure:
{
  "base": [
    "script.py",
  ],
  "machine": [
    "script.sh",
  ],
}
"""

import argparse
import json
import os
from pathlib import Path

import utils

RESERVED_PREFIXES = [
    "after_",
    "before_",
    "once_",
    "onchange_",
    "once_after_",
    "once_before_",
    "after_onchange_",
    "before_onchange_",
]


def main(prefix: str) -> None:
    base = load_scripts("base")
    machine = load_scripts("machine")
    scripts: list[Path] = []

    # filter scripts
    for script in base + machine:
        if prefix == "" and is_scheduled_script(script):
            continue  # skip scheduled scripts if no prefix
        if prefix and not script.name.startswith(prefix):
            continue  # skip non-matching prefix
        scripts.append(script)

    # debug info
    utils.debug("scripts", f"prefix: {prefix}")
    utils.debug("scripts", f"scripts: {len(scripts)}")
    for script in scripts:
        utils.debug("scripts", f"  - {script}")

    # run scripts
    for script in scripts:
        set_permissions(script)
        utils.execute_script(script)


def load_scripts(source: str) -> "list[Path]":
    chezmoi_data = os.environ.get("CHEZMOI_DATA", "")
    if not chezmoi_data:
        return find_scripts(source)

    try:
        data: dict[str, list[str]] = json.loads(chezmoi_data)
        return list([Path(s) for s in data[source]])
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid CHEZMOI_DATA: {chezmoi_data}") from e
    except KeyError as e:
        raise ValueError(f"{source} not found in data: {chezmoi_data}") from e
    except TypeError as e:
        raise ValueError(f"invalid source scripts list: {chezmoi_data}") from e


def find_scripts(source: str) -> "list[Path]":
    machine = utils.get_env("MACHINE", Path)
    machine_id = utils.get_env("MACHINE_ID", str)

    source_path = machine / "config" / "scripts"  # base
    if source == "machine":
        source_path = machine / "machines" / machine_id / "scripts"
    print(f"loading scripts from: {source_path}")

    scripts: list[Path] = []
    for script in source_path.iterdir():
        scripts.append(script)
    return scripts


def is_scheduled_script(script: Path) -> bool:
    filename = os.path.basename(script)
    return any(filename.startswith(prefix) for prefix in RESERVED_PREFIXES)


def set_permissions(script: Path) -> None:
    if os.name == "posix":
        os.chmod(script, 0o755)  # executable
    elif os.name == "nt":
        ...


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--prefix", nargs="?", type=str, help="script prefix filter"
    )

    args = parser.parse_args()
    utils.script_entrypoint("scripts", lambda: main(args.prefix or ""))
