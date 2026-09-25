#!/usr/bin/env python3
"""Check shell syntax and Unix script permissions without executing scripts."""

import os
from pathlib import Path

from _common import files, run

run("uv", "run", "--no-sync", "shellcheck", "--severity=error", *map(str, files("*.sh")))

print("\n==> Checking PowerShell syntax...", flush=True)
run("pwsh", "-NoProfile", "-File", str(Path(__file__).with_name("pwsh.ps1")))

if os.name == "nt":
    exit()  # not unix

for path in files("*.fish"):
    run("fish", "--no-config", "--no-execute", str(path))

for path in files("*/scripts/*"):
    if os.access(path, os.X_OK):
        continue  # executable
    raise SystemExit(f"Script is not executable: {path}")
