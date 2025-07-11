#!/usr/bin/env python3

__all__ = ["PackageManager", "execute_script", "run"]

import enum
import platform
import shutil
import subprocess
import sys
from pathlib import Path

WINDOWS = sys.platform.lower().startswith("win")
LINUX = sys.platform.lower().startswith("linux")
MACOS = sys.platform.lower().startswith("darwin")
UNIX = LINUX or MACOS


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
        if self == PackageManager.BREW:
            return platform.system().lower().startswith("darwin")  # macOS
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
            print(f"{self.value} is not supported")
            return False

    def install(self, package: str) -> None:
        if not self.is_available():
            raise RuntimeError(f"{self.value} is not available")

        if self == PackageManager.BREW:
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
            print(f"{self.value} failed to install {package}")


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
    if not UNIX and ".unix" in suffixes:
        return

    # Universal scripts
    print(f"running script: {script}")
    script = f"{sys.executable} {script}" if path.suffix == ".py" else script
    run(script)


def run(cmd: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    exe = shutil.which("powershell.exe") if WINDOWS else None
    return subprocess.run(cmd.strip(), shell=True, check=check, executable=exe)
