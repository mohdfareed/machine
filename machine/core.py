"""Core utilities and platform detection."""

from __future__ import annotations

import enum
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TypeVar

# Platform detection
WINDOWS = sys.platform.lower().startswith("win")
LINUX = sys.platform.lower().startswith("linux")
MACOS = sys.platform.lower().startswith("darwin")
WSL = shutil.which("wslinfo") is not None
CODESPACES = os.environ.get("CODESPACES", "") != ""
UNIX = LINUX or MACOS or WSL

T = TypeVar("T")


class Platform(enum.Enum):
    """Current platform identifier."""

    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    WSL = "wsl"
    CODESPACES = "codespaces"

    @classmethod
    def current(cls) -> Platform:
        """Get the current platform."""
        if CODESPACES:
            return cls.CODESPACES
        if WSL:
            return cls.WSL
        if MACOS:
            return cls.MACOS
        if LINUX:
            return cls.LINUX
        if WINDOWS:
            return cls.WINDOWS
        raise RuntimeError("Unknown platform")

    @classmethod
    def suffixes(cls) -> list[str]:
        """Get file suffixes that match current platform."""
        suffixes = []
        if UNIX:
            suffixes.append(".unix")
        if WINDOWS:
            suffixes.append(".win")
        if LINUX:
            suffixes.append(".linux")
        if MACOS:
            suffixes.append(".macos")
        if WSL:
            suffixes.append(".wsl")
        if CODESPACES:
            suffixes.append(".codespaces")
        return suffixes


class PackageManager(enum.Enum):
    """Supported package managers with install commands."""

    BREW = "brew"
    MAS = "mas"
    APT = "apt"
    SNAP = "snap"
    WINGET = "winget"
    SCOOP = "scoop"

    def __str__(self) -> str:
        return self.value

    def is_available(self) -> bool:
        """Check if the package manager binary exists."""
        return shutil.which(self.value) is not None

    def is_supported(self) -> bool:
        """Check if the package manager can be used on this platform."""
        if self.is_available():
            return True

        if self == PackageManager.BREW:
            return UNIX
        elif self == PackageManager.MAS:
            return PackageManager.BREW.is_supported()
        elif self == PackageManager.APT:
            return self.is_available()  # pre-installed on supported systems
        elif self == PackageManager.SNAP:
            return PackageManager.APT.is_supported()
        elif self == PackageManager.WINGET:
            return self.is_available()  # pre-installed on Windows
        elif self == PackageManager.SCOOP:
            return PackageManager.WINGET.is_supported()

        return False

    def install_command(self, package: str) -> str:
        """Get the install command for a package."""
        if self == PackageManager.BREW:
            return f"brew install {package}"
        elif self == PackageManager.MAS:
            return f"mas install {package}"
        elif self == PackageManager.APT:
            return f"sudo apt install -y {package}"
        elif self == PackageManager.SNAP:
            return f"sudo snap install {package}"
        elif self == PackageManager.WINGET:
            return f"winget install --accept-source-agreements --accept-package-agreements {package}"
        elif self == PackageManager.SCOOP:
            return f"scoop install {package}"

        raise NotImplementedError(f"{self.value} is not implemented")


# Global state
_dry_run = False
_debug = False


def set_dry_run(enabled: bool) -> None:
    """Enable or disable dry-run mode."""
    global _dry_run
    _dry_run = enabled


def set_debug(enabled: bool) -> None:
    """Enable or disable debug mode."""
    global _debug
    _debug = enabled


def is_dry_run() -> bool:
    """Check if dry-run mode is enabled."""
    return _dry_run


def is_debug() -> bool:
    """Check if debug mode is enabled."""
    return _debug


def run(cmd: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    """Run a shell command. Skipped in dry-run mode."""
    cmd = cmd.strip()
    exe = shutil.which("powershell.exe") if WINDOWS else None

    debug("run", cmd)
    if _dry_run:
        debug("run", "skipped (dry-run)")
        return subprocess.CompletedProcess(cmd, 0)

    try:
        return subprocess.run(cmd, shell=True, check=check, executable=exe)
    except subprocess.CalledProcessError as e:
        error(f"command failed (exit code {e.returncode}): {cmd}")
        if check:
            raise
        return subprocess.CompletedProcess(cmd, e.returncode)


def debug(source: str, msg: str) -> None:
    """Print a debug message if debug mode is enabled."""
    if _debug:
        print(f"[{source}] {msg}")


def error(msg: str) -> None:
    """Print an error message to stderr."""
    print(f"[error] {msg}", file=sys.stderr)


def info(msg: str) -> None:
    """Print an info message."""
    print(f":: {msg}")


def get_machine_root() -> Path:
    """Get the root directory of this repository."""
    return Path(__file__).parent.parent.resolve()
