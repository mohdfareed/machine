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
# - config and each machine/ can have an optional scripts/ folder
# - the scripts are executed using chezmoi's rules
# - .sh are executed on unix, .ps1 on windows, .py on all platforms
# - OR scripts ending with .win.*, .unix.*, .linux.*, .macos.* are
#   executed on the respective platforms; no suffix means all platforms

import json
import os
import sys


def main() -> None:
    base = load_scripts("base")
    machine = load_scripts("machine")

    for script in base + machine:
        print(f"script: {script}")  # TODO: implement execution logic


def load_scripts(source: str) -> list[str]:
    try:
        data = json.loads(os.environ.get("CHEZMOI_SCRIPTS", ""))
        return data.get(source, {}).get("scripts", [])
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid CHEZMOI_SCRIPTS: {e}") from e


if __name__ == "__main__":
    try:  # run script
        main()
    except KeyboardInterrupt:
        print("aborted!")
        sys.exit(1)
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)
