#!/usr/bin/env python3
"""Check the lockfile and installed development dependencies without syncing."""

from _common import run

run("uv", "lock", "--check")
run("uv", "sync", "--dev", "--check")
