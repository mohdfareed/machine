"""Machine setup automation - cross-platform dotfiles and package manager."""

from src.core import (
    CODESPACES,
    LINUX,
    MACOS,
    UNIX,
    WINDOWS,
    WSL,
    PackageManager,
    Platform,
    debug,
    error,
    info,
    run,
)

__all__ = [
    "Platform",
    "PackageManager",
    "WINDOWS",
    "LINUX",
    "MACOS",
    "WSL",
    "CODESPACES",
    "UNIX",
    "run",
    "debug",
    "error",
    "info",
]
