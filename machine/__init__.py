"""Machine setup automation - cross-platform dotfiles and package manager."""

from machine.core import (
    CODESPACES,
    LINUX,
    MACOS,
    UNIX,
    WINDOWS,
    WSL,
    Platform,
    debug,
    error,
    run,
)

__all__ = [
    "Platform",
    "WINDOWS",
    "LINUX",
    "MACOS",
    "WSL",
    "CODESPACES",
    "UNIX",
    "run",
    "debug",
    "error",
]
