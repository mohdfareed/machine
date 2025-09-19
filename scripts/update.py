#!/usr/bin/env python3
"""
System update orchestrator.

- Updates chezmoi configuration
- Updates packages via package managers
- Updates zinit plugins
- Updates neovim plugins
- Updates WSL (if on Windows)
"""

import argparse
import shutil

import utils


def main() -> None:
    update_chezmoi()
    update_packages()
    update_zinit()
    update_neovim()
    update_wsl()


def update_chezmoi() -> None:
    if not shutil.which("chezmoi"):
        return
    utils.run("chezmoi update", check=False)
    utils.run("chezmoi init --apply", check=False)


def update_packages() -> None:
    cmds: list[str] = []

    if utils.PackageManager.BREW.is_available():
        cmds += [
            "brew update",
            "brew upgrade",
            "brew cleanup -s",
        ]
    if utils.PackageManager.MAS.is_available():
        cmds += ["mas upgrade"]

    if utils.PackageManager.APT.is_available():
        cmds += [
            "sudo apt update",
            "sudo apt upgrade -y",
            "sudo apt autoremove -y",
        ]
    if utils.PackageManager.SNAP.is_available():
        cmds += ["sudo snap refresh"]

    if utils.PackageManager.WINGET.is_available():
        cmds += ["winget upgrade --all --silent"]
    if utils.PackageManager.SCOOP.is_available():
        cmds += [
            "scoop update",
            "scoop update *",
            "scoop cleanup *",
        ]

    for cmd in cmds:
        utils.run(cmd, check=False)


def update_zinit() -> None:
    if not shutil.which("zsh"):
        return
    utils.run("zinit self-update; zinit update", check=False)


def update_neovim() -> None:
    if not shutil.which("nvim"):
        return
    utils.run("nvim --headless '+Lazy! sync' +qa", check=False)


def update_wsl() -> None:
    if utils.WINDOWS:
        utils.run("wsl --update", check=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    args = parser.parse_args()
    utils.script_entrypoint("update", main)
