"""System update functionality.

Updates:
- Package managers (brew, apt, winget, etc.)
- Zinit plugins
- Neovim plugins
- WSL (on Windows)
"""

from __future__ import annotations

import shutil

from machine.core import WINDOWS, PackageManager, info, run


def update_all() -> None:
    """Run all updates."""
    update_packages()
    update_zinit()
    update_neovim()
    update_wsl()


def update_packages() -> None:
    """Update all available package managers."""
    commands: list[str] = []

    if PackageManager.BREW.is_available():
        info("updating Homebrew...")
        commands += [
            "brew update",
            "brew upgrade",
            "brew cleanup -s",
        ]

    if PackageManager.MAS.is_available():
        info("updating Mac App Store apps...")
        commands += ["mas upgrade"]

    if PackageManager.APT.is_available():
        info("updating apt packages...")
        commands += [
            "sudo apt update",
            "sudo apt upgrade -y",
            "sudo apt autoremove -y",
        ]

    if PackageManager.SNAP.is_available():
        info("updating snap packages...")
        commands += ["sudo snap refresh"]

    if PackageManager.WINGET.is_available():
        info("updating winget packages...")
        commands += ["winget upgrade --all --silent"]

    if PackageManager.SCOOP.is_available():
        info("updating scoop packages...")
        commands += [
            "scoop update",
            "scoop update *",
            "scoop cleanup *",
        ]

    for cmd in commands:
        run(cmd, check=False)


def update_zinit() -> None:
    """Update zinit and plugins."""
    if not shutil.which("zsh"):
        return

    info("updating zinit plugins...")
    # Run in zsh to have zinit available
    run(
        'zsh -c "source ~/.zshrc && zinit self-update && zinit update"',
        check=False,
    )


def update_neovim() -> None:
    """Update Neovim plugins via Lazy."""
    if not shutil.which("nvim"):
        return

    info("updating Neovim plugins...")
    run("nvim --headless '+Lazy! sync' +qa", check=False)


def update_wsl() -> None:
    """Update WSL on Windows."""
    if not WINDOWS:
        return

    info("updating WSL...")
    run("wsl --update", check=False)
