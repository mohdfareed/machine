"""Runtime settings, machine configuration, and operation results."""

from enum import StrEnum
from importlib.metadata import metadata
from pathlib import Path
from typing import ClassVar, Self

import typer
from pydantic import BaseModel, model_validator

# =============================================================================
# MARK: Settings
# =============================================================================

_meta = metadata("machine")


class Settings:
    """Mutable runtime settings."""

    name: ClassVar[str] = _meta["Name"]
    version: ClassVar[str] = _meta["Version"]
    description: ClassVar[str] = _meta["Summary"]
    app_dir: ClassVar[Path] = Path(typer.get_app_dir("mc"))

    debug: bool = False
    dry_run: bool = False
    home: Path = Path(__file__).resolve().parents[1]

    @property
    def log_file(self) -> Path:
        """Return the rotating application log path."""
        return self.app_dir / f"{self.name}.log"

    @property
    def state_file(self) -> Path:
        """Return the script-run state path."""
        return self.app_dir / "state.json"

    @property
    def machine_file(self) -> Path:
        """Return the saved current-machine selection path."""
        return self.app_dir / "machine.txt"


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

    name: str = ""
    platforms: list[Platform] | None = None
    script: str | None = None

    # macOS packages.
    brew: str | None = None
    cask: str | None = None
    mas: int | None = None

    # Linux packages.
    apt: str | None = None
    snap: str | None = None

    # Windows packages.
    winget: str | None = None
    scoop: str | None = None

    def applies_to(self, platform: Platform) -> bool:
        """Return True when this package should be considered on *platform*."""
        return self.platforms is None or any(platform.is_a(target) for target in self.platforms)

    @model_validator(mode="after")
    def _check_source(self) -> Self:
        # Collect names from the declared package sources.
        name_sources: list[str | None] = [
            self.brew,
            self.cask,
            self.apt,
            self.snap,
            self.winget,
            self.scoop,
            str(self.mas),
        ]

        # Require an install source and infer an omitted package name.
        if not any(s is not None for s in [*name_sources, self.script]):
            raise ValueError(f"Package '{self.name}' has no install source")
        if not self.name:
            self.name = next(s for s in name_sources if s is not None)

        return self


class Module(BaseModel):
    """A composable unit of configuration."""

    name: str = ""
    depends: list[str] = []
    scripts: list[str] = []
    files: list[FileMapping] = []
    overrides: list[FileMapping] = []
    packages: list[Package] = []


class Machine(BaseModel):
    """Complete machine declaration."""

    pkg_managers: list[PkgManager] = []
    modules: list[str] = []
    scripts: list[str] = []
    files: list[FileMapping] = []
    packages: list[Package] = []


# =============================================================================
# MARK: Operation Results
# =============================================================================


class Failure(BaseModel):
    """An operation failure with its owner, affected item, and reason."""

    module: str
    item: str
    detail: str


class FileResult(BaseModel):
    """File deployment counts and failures, including permission-only changes."""

    created: int
    failures: list[Failure]
