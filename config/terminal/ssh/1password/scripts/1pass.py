#!/usr/bin/env python3
"""Set up 1Password."""

import subprocess


def main() -> None:
    print("1password: signing in...")
    subprocess.run("op signin", check=True)


if __name__ == "__main__":
    main()
