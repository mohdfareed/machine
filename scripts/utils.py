#!/usr/bin/env python3

__all__ = ["PackageManager", "run", "execute_script"]

import enum
import platform
import shutil
import subprocess
import sys
from pathlib import Path


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
        run(command)


def run(cmd: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(cmd.strip(), shell=True, check=check)


def execute_script(script: str) -> None:
    system = platform.system().lower()
    path = Path(script)
    suffixes = [s.lower() for s in path.suffixes]

    # PowerShell scripts (.ps1 and .win.ps1)
    if any(s == ".ps1" for s in suffixes):
        run(f"powershell -ExecutionPolicy Bypass -File {script}")
        return

    # Windows-specific executables (.win)
    if suffixes and suffixes[-1] == ".win" and system == "windows":
        run(script)
        return

    # Unix-like scripts (.sh, .linux, .macos, .unix)
    if (
        suffixes
        and suffixes[-1] in {".sh", ".linux", ".macos", ".unix"}
        and system in {"linux", "darwin"}
    ):
        run(script)
        return

    # Python scripts
    if suffixes and suffixes[-1] == ".py":
        run(f"{sys.executable} {script}")
        return

    try:  # Fallback to executing directly if executable
        run(script)
    except (OSError, subprocess.CalledProcessError):
        print(f"Skipping unsupported script: {script}")
