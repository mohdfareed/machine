#!/usr/bin/env python3
"""
Cross-platform script runner.
Reads JSON from CHEZMOI_DATA and runs scripts using the appropriate shell.

Expected JSON structure:
{
    "base": [
        "script.py",
    ],
    "machine": [
        "script.sh",
    ]
}
"""

import argparse
import json
import os
import sys

from utils import execute_script

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

    for script in base + machine:
        if prefix == "" and is_scheduled_script(script):
            continue

        set_permissions(script)
        execute_script(script)


def load_scripts(source: str) -> list[str]:
    try:
        data = json.loads(os.environ.get("CHEZMOI_DATA", ""))
        return data.get(source, {})
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid CHEZMOI_DATA: {e}") from e


def is_scheduled_script(script: str) -> bool:
    filename = os.path.basename(script)
    return any(filename.startswith(prefix) for prefix in RESERVED_PREFIXES)


def set_permissions(script: str) -> None:
    if os.name == "posix":
        os.chmod(script, 0o755)  # executable
    elif os.name == "nt":
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", nargs="?", type=str)
    args = parser.parse_args()

    try:  # run script
        main(args.prefix or "")
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as error:
        print(f"scripts error: {error}", file=sys.stderr)
        sys.exit(1)
