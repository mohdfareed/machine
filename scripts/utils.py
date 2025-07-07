#!/usr/bin/env python3

__all__ = ["PackageManager", "run"]

import enum
import shutil
import subprocess
import sys


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
            return sys.platform.startswith("darwin")  # macOS
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
