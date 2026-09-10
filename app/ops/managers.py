"""Package manager configuration, validation, and installed-package queries."""

import shutil
import subprocess
from dataclasses import dataclass
from typing import Literal

from app.env import PLATFORM
from app.models import PkgManager, Platform

# =============================================================================
# MARK: Configure Managers
# =============================================================================

type PackageSource = Literal["brew", "cask", "apt", "snap", "winget", "scoop", "mas"]


@dataclass(frozen=True, slots=True)
class ManagerConfig:
    """Define a package source's executable and installation command."""

    binary: str
    install_cmd: str


PLATFORM_SOURCES: dict[Platform, tuple[PackageSource, ...]] = {
    Platform.MACOS: ("cask", "brew", "mas"),
    Platform.LINUX: ("apt", "snap", "brew"),
    Platform.WINDOWS: ("winget", "scoop"),
}
MANAGER_CONFIGS: dict[PackageSource, ManagerConfig] = {
    "brew": ManagerConfig(binary="brew", install_cmd="brew install {}"),
    "cask": ManagerConfig(binary="brew", install_cmd="brew install --cask {}"),
    "apt": ManagerConfig(binary="apt", install_cmd="sudo apt install -y {}"),
    "snap": ManagerConfig(binary="snap", install_cmd="sudo snap install {}"),
    "winget": ManagerConfig(
        binary="winget",
        install_cmd="winget install --accept-source-agreements --accept-package-agreements {}",
    ),
    "scoop": ManagerConfig(binary="scoop", install_cmd="scoop install {}"),
    "mas": ManagerConfig(binary="mas", install_cmd="mas install {}"),
}

# =============================================================================
# MARK: Validate Manager Declarations
# =============================================================================


def validate_managers(managers: list[PkgManager]) -> None:
    """Validate explicit manager declarations before running setup scripts."""
    supported = {
        MANAGER_CONFIGS[source].binary
        for platform, sources in PLATFORM_SOURCES.items()
        if PLATFORM.is_a(platform)
        for source in sources
    }

    for manager in managers:
        if manager not in supported:
            raise ValueError(f"{manager} is not supported on {PLATFORM}")

    # Check setup prerequisites after platform compatibility.
    if PkgManager.MAS in managers and PkgManager.BREW not in managers:
        raise ValueError("mas requires brew in the machine's declared package managers")
    if PkgManager.APT in managers and not shutil.which("apt"):
        raise ValueError("apt must already be installed")
    if PkgManager.SNAP in managers and not shutil.which("snap") and PkgManager.APT not in managers:
        raise ValueError("Installing snap requires apt in the machine's declared package managers")


# =============================================================================
# MARK: Check Installation Success
# =============================================================================


def install_succeeded(manager: PackageSource | None, rc: int, output: bytes | bytearray) -> bool:
    """Accept successful exits and manager-specific already-installed results."""
    if rc == 0:
        return True
    if manager != "winget":
        return False

    # Accept winget's already-installed result when no upgrade is available.
    text = output.decode(errors="replace").lower()
    return "found an existing package already installed" in text and any(
        msg in text
        for msg in (
            "no available upgrade found",
            "no newer package versions are available from the configured sources",
        )
    )


# =============================================================================
# MARK: Query Package Presence
# =============================================================================


def source_installed(source: PackageSource, value: str | int) -> bool:
    """Check whether the selected source manages the requested package."""
    match source:
        case "brew" | "cask":
            cmd = ["brew", "list", "--formula" if source == "brew" else "--cask", str(value)]

        case "mas":
            lines = _query(["mas", "list"], check=True).stdout.splitlines()
            return any(line.split()[0] == str(value) for line in lines if line.strip())

        case "apt":
            result = _query(["dpkg-query", "-W", "-f=${Status}", str(value)])
            return result.returncode == 0 and "install ok installed" in result.stdout.lower()

        case "snap" | "scoop":
            cmd = [source, "list", str(value)]

        case "winget":
            # --exact is case-sensitive; compare the full ID ourselves after the ID-filtered query.
            result = _query(["winget", "list", "--id", str(value)])
            return result.returncode == 0 and str(value).casefold() in {
                field.casefold() for field in result.stdout.split()
            }

        case _:
            raise AssertionError(f"Unhandled package source: {source}")

    return _query(cmd).returncode == 0


def _query(cmd: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    # Resolve Windows shims before running the bounded presence query.
    executable = shutil.which(cmd[0])
    if executable is None:
        raise FileNotFoundError(f"Manager query executable not found: {cmd[0]}")

    return subprocess.run(
        [executable, *cmd[1:]], capture_output=True, text=True, timeout=30, check=check
    )
