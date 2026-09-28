#!/usr/bin/env python3
"""Prepare, commit, and tag a release."""

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
    if not output("git", "branch", "--show-current"):
        sys.exit("Switch to a branch before releasing.")

    print("\n==> Bumping version...", flush=True)
    run("uv", "version", "--bump", bump.value)
    version = output("uv", "version", "--short")
    tag = f"v{version}"

    if output("git", "tag", "--list", tag):
        sys.exit(f"Tag {tag} already exists.")

    print("\n==> Running checks...", flush=True)
    check_script = Path(__file__).resolve().with_name("fix.py")
    run(sys.executable, str(check_script))

    print(f"\n==> Creating release {tag}...", flush=True)
    run("git", "add", "--all")
    run("git", "commit", "-m", f"chore: release {tag}")
    run("git", "tag", "-a", tag, "-m", f"Release {tag}")

    print(f"\nPush with: git push --follow-tags")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bump", choices=[item.value for item in Bump])
    bump = Bump(parser.parse_args().bump)

    main(bump)
