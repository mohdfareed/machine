#!/usr/bin/env python3
"""Check code quality, tests, and spelling."""

from _common import run

run("uv", "run", "--no-sync", "ruff", "format", "--check", ".")
run("uv", "run", "--no-sync", "ruff", "check", ".")
run("uv", "run", "--no-sync", "pyright")
run("uv", "run", "--no-sync", "pytest", "-q")
run("uv", "run", "--no-sync", "typos")
