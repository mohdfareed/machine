#!/usr/bin/env python3
from __future__ import annotations

__all__ = ["PackageManager", "execute_script", "run", "debug", "error"]

import enum
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Callable as TypingCallable
from typing import Optional, TypeVar, cast

WINDOWS = sys.platform.lower().startswith("win")
LINUX = sys.platform.lower().startswith("linux")
MACOS = sys.platform.lower().startswith("darwin")
WSL = shutil.which("wslinfo") is not None
CODESPACES = os.environ.get("CODESPACES", default=False) is not False
UNIX = LINUX or MACOS or WSL

T = TypeVar("T")


class ExitCode(enum.IntEnum):
    SUCCESS = 0
    ERROR = 1
    INTERRUPT = 130


class PackageManager(enum.Enum):
    """Enum of supported package managers with install commands."""

    BREW = "brew"
    MAS = "mas"

    APT = "apt"
    SNAP = "snap"

    WINGET = "winget"
    SCOOP = "scoop"

    def __str__(self) -> str:
        return self.value

    def is_available(self) -> bool:
        return shutil.which(self.value) is not None

    def is_supported(self) -> bool:
        if self.is_available():
            return True

        if self == PackageManager.BREW:
            return UNIX  # unix
        elif self == PackageManager.MAS:
            return PackageManager.BREW.is_supported()  # brew

        elif self == PackageManager.APT:
            return self.is_available()  # pre-installed
        elif self == PackageManager.SNAP:
            return PackageManager.APT.is_supported()  # apt

        elif self == PackageManager.WINGET:
            return self.is_available()  # pre-installed
        elif self == PackageManager.SCOOP:
            return PackageManager.WINGET.is_supported()  # winget

        else:
            raise NotImplementedError(f"{self.value} is not implemented")

    def install(self, package: str) -> None:
        if not self.is_available():
            raise RuntimeError(f"{self.value} is not available")

        if self == PackageManager.BREW:
            os.environ["HOMEBREW_NO_AUTO_UPDATE"] = "1"
            command = f"brew install {package}"
        elif self == PackageManager.MAS:
            command = f"mas install {package}"

        elif self == PackageManager.APT:
            command = f"sudo apt install -y {package}"
        elif self == PackageManager.SNAP:
            command = f"sudo snap install {package}"

        elif self == PackageManager.SCOOP:
            command = f"scoop install {package}"
        elif self == PackageManager.WINGET:
            command = f"winget install {package}"

        else:
            raise NotImplementedError(f"{self.value} is not implemented")

        try:
            run(command)
        except Exception as ex:
            error(f"{self.value} failed to install {package}: {ex}")

        if self == PackageManager.BREW:
            os.environ.pop("HOMEBREW_NO_AUTO_UPDATE", None)


def script_entrypoint(src: str, func: Callable[..., None]) -> None:
    """Standard script entrypoint with error handling."""
    debug("cli", "debug mode enabled")
    if get_env("DRY_RUN", default=False):
        debug("cli", "dry-run mode enabled")

    try:
        func()
        sys.exit(ExitCode.SUCCESS)

    except KeyboardInterrupt:
        debug("cli", "aborted!")
        sys.exit(ExitCode.INTERRUPT)

    except subprocess.CalledProcessError as e:
        error(f"{src}: {e}")
        if get_env("DEBUG", default=False):
            raise
        sys.exit(e.returncode)

    except Exception as e:
        error(f"{src}: {e}")
        if get_env("DEBUG", default=False):
            raise
        sys.exit(ExitCode.ERROR)


def execute_script(script: Path) -> None:
    """Execute a script file, supports suffixes-based filtering."""
    suffixes = [s.lower() for s in script.suffixes]

    # OS-specific filters
    if not WINDOWS and ".win" in suffixes:
        return
    if not LINUX and ".linux" in suffixes:
        return
    if not MACOS and ".macos" in suffixes:
        return
    if not WSL and ".wsl" in suffixes:
        return
    if not CODESPACES and ".codespaces" in suffixes:
        return
    if not UNIX and ".unix" in suffixes:
        return

    cmd = str(script)
    if script.suffix == ".py":
        cmd = f"{sys.executable} {script}"
    elif script.suffix == ".ps1" and WINDOWS:
        cmd = f'powershell -ExecutionPolicy Bypass -File "{script}"'

    print(f"running script: {cmd}")
    run(cmd)


def run(cmd: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    """Run a shell command. If command is not executed if DRY_RUN is set."""

    cmd = cmd.strip()
    exe = shutil.which("powershell.exe") if WINDOWS else None

    debug("cmd", cmd)
    if get_env("DRY_RUN", default=False):
        debug("cmd", "skipped (dry-run)")
        return subprocess.CompletedProcess(cmd, 0)

    try:
        return subprocess.run(cmd, shell=True, check=check, executable=exe)
    except subprocess.CalledProcessError as e:
        error(f"command failed (exit code {e.returncode}): {cmd}")
        if check:
            raise e

        return subprocess.CompletedProcess(
            cmd, e.returncode, stdout=e.stdout, stderr=e.stderr
        )


def get_env(
    var: str,
    parser: TypingCallable[[str], T] = cast(TypingCallable[[str], T], str),
    default: Optional[T] = None,
) -> T:
    """Get an environment variable or raise if None."""
    value: str = os.environ.get(var, str(default or ""))
    if not value and default is None:
        raise RuntimeError(f"{var} environment variable is not set")

    try:
        return parser(value)
    except Exception as e:
        raise TypeError(f"failed to cast {var}={value!r} to {parser}: {e}")


def debug(source: str, msg: str) -> None:
    """Print a debug message if DEBUG environment variable is set."""
    if get_env("DEBUG", default=False):
        print(f"[{source}] {msg}")


def error(msg: str) -> None:
    """Print an error message to stderr."""
    print(f"[error] {msg}", file=sys.stderr)


if __name__ == "__main__":
    debug("utils", "running utils module")
    print(f"python: {sys.executable} ({sys.version})")
    print(f"platform: {sys.platform} (WSL={WSL}, CODESPACES={CODESPACES})")

    print("available package managers:")
    for pm in PackageManager:
        supported = "" if pm.is_available() else "not "
        available = "available" if pm.is_available() else "not available"
        print(f"  - {pm} -> available: {available}, supported: {supported}")

    error("this module is not meant to be run directly")
    exit(ExitCode.ERROR)
