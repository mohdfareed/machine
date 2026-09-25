#!/usr/bin/env python3
"""Command execution and file discovery for repository checks."""

import subprocess
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(*command: str) -> None:
    """Run from the repository root, preserving tool output and failure status."""
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)


def files(pattern: str) -> Iterator[Path]:
    """Find source files in the application, configuration, and scripts."""
    for folder in ("app", "config", "machines", "scripts"):
        yield from (ROOT / folder).rglob(pattern)
