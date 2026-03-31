#!/usr/bin/env python3

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Open Machine Private
# @raycast.mode silent

# Optional parameters:
# @raycast.packageName Machine

import os
import subprocess
import sys
from pathlib import Path

from _machine import REPO_ROOT, open_path

if sys.platform.startswith("win"):
    runners = [
        ["pwsh", "-NoLogo", "-NoProfile", "-Command", "mc private"],
        ["pwsh", "-NoLogo", "-NoProfile", "-Command", "uv run mc private"],
    ]
else:
    shell = os.environ.get("SHELL", "/bin/sh")
    runners = [
        [shell, "-lc", "mc private"],
        [shell, "-lc", "uv run mc private"],
    ]

for runner in runners:
    proc = subprocess.run(
        runner,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if proc.returncode == 0:
        output = proc.stdout.strip()
        if output:
            open_path(Path(output).expanduser())
            raise SystemExit

raise SystemExit("Could not resolve MC_PRIVATE via `mc private`.")
