#!/usr/bin/env python3
"""Run all repository checks, stopping on the first failure."""

import sys
from pathlib import Path

from checks._common import run

print("==> Checking scripts...", flush=True)
run(sys.executable, str(Path(__file__).with_name("checks") / "scripts.py"))

print("\n==> Checking code...", flush=True)
run(sys.executable, str(Path(__file__).with_name("checks") / "code.py"))

print("\n==> Checking dependencies...", flush=True)
run(sys.executable, str(Path(__file__).with_name("checks") / "dependencies.py"))

print("\n==> All checks passed!")
