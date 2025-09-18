#!/usr/bin/env python3

__all__ = ["PackageManager", "execute_script", "run", "debug", "error"]

import enum
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

WINDOWS = sys.platform.lower().startswith("win")
LINUX = sys.platform.lower().startswith("linux")
MACOS = sys.platform.lower().startswith("darwin")
WSL = shutil.which("wslinfo") is not None
UNIX = LINUX or MACOS or WSL


class ExitCode(enum.IntEnum):
    SUCCESS = 0
    ERROR = 1
    INTERRUPT = 130


class PackageManager(enum.Enum):
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
        except:
            error(f"{self.value} failed to install {package}")

        if self == PackageManager.BREW:
            os.environ.pop("HOMEBREW_NO_AUTO_UPDATE", None)


def script_entrypoint(src: str, func: Callable[..., None]) -> None:
    try:
        func()
        sys.exit(ExitCode.SUCCESS)

    except KeyboardInterrupt:
        print("aborted!")
        sys.exit(ExitCode.INTERRUPT)

    except subprocess.CalledProcessError as e:
        error(f"{src}: {e}")
        if os.environ.get("DEBUG"):
            raise
        sys.exit(e.returncode)

    except Exception as e:
        error(f"{src}: {e}")
        if os.environ.get("DEBUG"):
            raise
        sys.exit(ExitCode.ERROR)


def execute_script(script: str) -> None:
    path = Path(script)
    suffixes = [s.lower() for s in path.suffixes]

    # OS-specific scripts
    if not WINDOWS and ".win" in suffixes:
        return
    if not LINUX and ".linux" in suffixes:
        return
    if not MACOS and ".macos" in suffixes:
        return
    if not WSL and ".wsl" in suffixes:
        return
    if not UNIX and ".unix" in suffixes:
        return

    # Universal scripts
    print(f"running script: {script}")
    if path.suffix == ".py":
        script = f"{sys.executable} {script}"
    elif path.suffix == ".ps1" and WINDOWS:
        script = f'powershell -ExecutionPolicy Bypass -File "{script}"'
    run(script)


def run(cmd: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    cmd = cmd.strip()
    dry_run = os.environ.get("DRY_RUN")
    exe = shutil.which("powershell.exe") if WINDOWS else None

    debug("cmd", f"{exe} {cmd}")
    if dry_run:
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


def debug(source: str, msg: str) -> None:
    if os.environ.get("DEBUG"):
        print(f"[{source}] {msg}")


def error(msg: str) -> None:
    print(f"[error] {msg}", file=sys.stderr)
