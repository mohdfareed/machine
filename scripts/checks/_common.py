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


def output(*args):
    """Run from the repository root and return the output as a string."""
    return subprocess.check_output(args, text=True).strip()


def files(pattern: str) -> Iterator[Path]:
    """Find source files in the application, configuration, and scripts."""
    for folder in ("app", "config", "machines", "scripts"):
        yield from (ROOT / folder).rglob(pattern)
