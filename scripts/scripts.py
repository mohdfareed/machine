#!/usr/bin/env python3
"""
Cross-platform script runner.
Reads JSON from CHEZMOI_PACKAGES and installs scripts using
the specified script managers.

Expected JSON structure:
{
    [
        "path/to/script1.py"
    ]
}
"""

# TODO: refactor scripts system as follows:
# - .sh are executed on unix, .ps1 on windows, .py on all platforms
# - OR scripts ending with .win.*, .unix.*, .linux.*, .macos.* are
#   executed on the respective platforms; no suffix means all platforms

import argparse
import json
import os
import sys

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
        if not script.startswith(prefix):
            continue
        if prefix == "" and is_scheduled_script(script):
            continue

        # TODO: implement execution logic
        print(f"running script: {script}")


def load_scripts(source: str) -> list[str]:
    try:
        data = json.loads(os.environ.get("CHEZMOI_DATA", ""))
        return data.get(source, {})
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid CHEZMOI_DATA: {e}") from e


def is_scheduled_script(script: str) -> bool:
    return any(script.startswith(prefix) for prefix in RESERVED_PREFIXES)


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
