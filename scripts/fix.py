#!/usr/bin/env python3
"""Run all automated fixes, then verify and check."""

import os
import sys
from pathlib import Path

from checks._common import files, run

print("==> Upgrading dependencies...", flush=True)
run("uv", "lock", "--upgrade")
run("uv", "sync", "--dev", "--locked")

print("\n==> Formatting and auto-fixing...", flush=True)
run("uv", "run", "ruff", "check", "--fix", ".")
run("uv", "run", "ruff", "format", ".")

print("\n==> Fixing spelling...", flush=True)
run("uv", "run", "typos", "--write-changes")

print("\n==> Fixing script...", flush=True)
for path in files("*/scripts/*"):
    if os.name != "nt" and not os.access(path, os.X_OK):
        run("chmod", "+x", str(path))

print()  # verify
run(sys.executable, str(Path(__file__).with_name("check.py")))
