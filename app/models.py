"""Machine configuration data shapes."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, PrivateAttr

# =============================================================================
# MARK: Enums
# =============================================================================


class Platform(StrEnum):
    """Supported platforms."""

    MACOS = "macos"
    LINUX = "linux"
    WINDOWS = "windows"
    WSL = "wsl"
    UNIX = "unix"  # macOS, Linux, or WSL.

    def is_a(self, other: "Platform") -> bool:
        """Match this platform to itself or a broader family, never the reverse."""
        return (
            self == other
            or (other == Platform.UNIX and self in {Platform.MACOS, Platform.LINUX, Platform.WSL})
            or (self == Platform.WSL and other == Platform.LINUX)
        )


class PkgManager(StrEnum):
    """Package managers explicitly enabled by a machine manifest."""

    BREW = "brew"
    MAS = "mas"
    APT = "apt"
    SNAP = "snap"
    WINGET = "winget"
    SCOOP = "scoop"


type PackageSource = Literal["brew", "cask", "apt", "snap", "winget", "scoop", "mas"]
"""Package source identifiers carried by resolved declarations."""


# =============================================================================
# MARK: Models
# =============================================================================


class FileMapping(BaseModel):
    """A config file or directory to symlink."""

    source: str
    target: str
    mode: int | None = None
    platforms: list[Platform] | None = None

    def applies_to(self, platform: Platform) -> bool:
        """Return True when this file mapping should be considered on *platform*."""
        return self.platforms is None or any(platform.is_a(target) for target in self.platforms)


class Package(BaseModel):
    """A package with optional per-manager install names."""

    model_config = ConfigDict(extra="forbid")

    name: str = ""
    platforms: list[Platform] | None = None
    cmd: str | None = None
    up_cmd: str | Literal[True] | None = None

    # macOS packages.
    brew: str | None = None
    cask: str | None = None
    mas: int | None = None

    # Linux packages.
    apt: str | None = None
    snap: str | None = None
    snap_classic: bool = False

    # Windows packages.
    winget: str | None = None
    scoop: str | None = None

    @property
    def selected_source(self) -> PackageSource | None:
        """Source chosen by the loader, excluded from declaration arguments."""
        return self._selected_source

    @selected_source.setter
    def selected_source(self, source: PackageSource | None) -> None:
        """Store the loader's source choice."""
        self._selected_source = source

    @property
    def sources(self) -> dict[PackageSource, str | int]:
        """Map external package-source identifiers to their configured values."""
        values: dict[PackageSource, str | int | None] = {
            "brew": self.brew,
            "cask": self.cask,
            "apt": self.apt,
            "snap": self.snap,
            "winget": self.winget,
            "scoop": self.scoop,
            "mas": self.mas,
        }
        return {source: value for source, value in values.items() if value is not None}

    def applies_to(self, platform: Platform) -> bool:
        """Return True when this package should be considered on *platform*."""
        return self.platforms is None or any(platform.is_a(target) for target in self.platforms)

    _selected_source: PackageSource | None = PrivateAttr(default=None)


class Module(BaseModel):
    """A composable unit of configuration."""

    name: str = ""
    depends: list[str] = []
    scripts: list[str] = []
    files: list[FileMapping] = []
    overrides: list[FileMapping] = []
    packages: list[Package] = []


class Machine(BaseModel):
    """Machine declaration, or combined configuration returned by load_machine()."""

    pkg_managers: list[PkgManager] = []
    modules: list[str] = []
    scripts: list[str] = []
    files: list[FileMapping] = []
    packages: list[Package] = []
