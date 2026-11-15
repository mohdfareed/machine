#!/usr/bin/env python3
"""Validate, commit, and tag a version release on main."""

import argparse
import os
import sys
from enum import StrEnum
from pathlib import Path

from checks._common import output, run


class Bump(StrEnum):
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"


def main(bump: Bump):
    os.chdir(output("git", "rev-parse", "--show-toplevel"))
    if output("git", "branch", "--show-current") != "main":
        sys.exit("Switch to main before releasing.")
    if output("git", "status", "--porcelain"):
        sys.exit("Commit or stash all changes before releasing.")

    # Check the release tag before changing the version.
    version = output("uv", "version", "--bump", bump.value, "--dry-run", "--short")
    tag = f"v{version}"
    if output("git", "tag", "--list", tag):
        sys.exit(f"Tag {tag} already exists.")

    # Bump and validate without upgrading dependencies or fixing files.
    print(f"\n==> Preparing release {tag}...", flush=True)
    run("uv", "version", "--bump", bump.value, "--no-sync")
    run("uv", "sync", "--dev", "--locked")
    run(sys.executable, str(Path(__file__).resolve().with_name("check.py")))

    # Commit only the release version and create its annotated tag.
    run("git", "add", "--", "pyproject.toml", "uv.lock")
    run("git", "commit", "-m", f"chore: release {tag}")
    run("git", "tag", "-a", tag, "-m", f"Release {tag}")
    print("\nPush with: git push --atomic origin main " + tag)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bump", choices=[item.value for item in Bump])
    bump = Bump(parser.parse_args().bump)

    main(bump)
