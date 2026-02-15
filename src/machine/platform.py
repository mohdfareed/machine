"""Platform detection."""

import os
import shutil
import sys
from enum import StrEnum


class Platform(StrEnum):
    """Supported platforms."""

    MACOS = "macos"
    LINUX = "linux"
    WINDOWS = "windows"
    WSL = "wsl"
    CODESPACES = "codespaces"


def detect() -> Platform:
    """Detect the current platform."""
    if os.environ.get("CODESPACES"):
        return Platform.CODESPACES
    if shutil.which("wslinfo"):
        return Platform.WSL
    match sys.platform:
        case p if p.startswith("darwin"):
            return Platform.MACOS
        case p if p.startswith("linux"):
            return Platform.LINUX
        case p if p.startswith("win"):
            return Platform.WINDOWS
        case _:
            raise RuntimeError(f"Unsupported platform: {sys.platform}")


PLATFORM = detect()
"""Current platform, detected at import time."""

is_macos = PLATFORM == Platform.MACOS
is_linux = PLATFORM in {Platform.LINUX, Platform.WSL, Platform.CODESPACES}
is_windows = PLATFORM == Platform.WINDOWS
is_wsl = PLATFORM == Platform.WSL
is_unix = not is_windows
