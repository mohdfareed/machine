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

    if os.environ.get("DEBUG"):
        print(f"prefix: {prefix}")
        print(f"base scripts: {len(base)}")
        for s in base:
            print(f"  - {s}")
        print(f"machine scripts: {len(machine)}")
        for s in machine:
            print(f"  - {s}")

    for script in base + machine:
        if prefix == "" and is_scheduled_script(script):
            continue

        set_permissions(script)
        utils.execute_script(script)


def load_scripts(source: str) -> list[str]:
    try:
        chezmoi_data = os.environ.get("CHEZMOI_DATA", "")
        data: dict = json.loads(chezmoi_data)
        return list(data[source])
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid CHEZMOI_DATA: {chezmoi_data}") from e
    except KeyError as e:
        raise ValueError(f"source '{source}' not found in data: {data}") from e
    except TypeError as e:
        raise ValueError(f"invalid source scripts list: {data[source]}") from e


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
