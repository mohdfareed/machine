"""Machine manifest models and loaders."""

import importlib.util
from pathlib import Path
from typing import Self

from pydantic import BaseModel, model_validator

# MARK: Models


class Dotfile(BaseModel):
    """A config file or directory to symlink."""

    source: str  # relative to repo root
    target: str  # absolute or ~ path


class Package(BaseModel):
    """A package with per-manager install names."""

    name: str
    brew: str | None = None
    apt: str | None = None
    snap: str | None = None
    winget: str | None = None
    scoop: str | None = None
    mas: int | None = None
    script: str | None = None

    @model_validator(mode="after")
    def _check_source(self) -> Self:
        sources = [
            self.brew, self.apt, self.snap,
            self.winget, self.scoop, self.script,
        ]
        if self.mas is None and not any(s is not None for s in sources):
            raise ValueError(f"Package '{self.name}' has no install source")
        return self


class MachineManifest(BaseModel):
    """Complete machine declaration."""

    dotfiles: list[Dotfile] = []
    packages: list[Package] = []


# MARK: Package Helpers


def brew(*names: str) -> list[Package]:
    """Create brew packages. Include flags in the name: 'pkg --flag'."""
    return [Package(name=n.split()[0], brew=n) for n in names]


def cask(*names: str) -> list[Package]:
    """Create brew cask packages."""
    return [Package(name=n.split()[0], brew=f"{n} --cask") for n in names]


def apt(*names: str) -> list[Package]:
    """Create apt packages."""
    return [Package(name=n.split()[0], apt=n) for n in names]


def snap(*names: str) -> list[Package]:
    """Create snap packages."""
    return [Package(name=n.split()[0], snap=n) for n in names]


def winget(*names: str) -> list[Package]:
    """Create winget packages."""
    return [Package(name=n.split()[0], winget=n) for n in names]


def scoop(*names: str) -> list[Package]:
    """Create scoop packages."""
    return [Package(name=n.split()[0], scoop=n) for n in names]


def mas(**apps: int) -> list[Package]:
    """Create Mac App Store packages: name=app_id."""
    return [Package(name=k, mas=v) for k, v in apps.items()]


# MARK: Loader


def load_manifest(machine_id: str, root: Path) -> MachineManifest:
    """Load a machine manifest from machines/<id>/manifest.py."""
    path = root / "machines" / machine_id / "manifest.py"
    if not path.exists():
        raise FileNotFoundError(f"No manifest: {path}")

    spec = importlib.util.spec_from_file_location(
        f"machines.{machine_id}.manifest", path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load: {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "manifest"):
        raise AttributeError(f"Missing 'manifest' in {path}")

    result = module.manifest
    if not isinstance(result, MachineManifest):
        raise TypeError(f"'manifest' must be MachineManifest, got {type(result)}")

    return result
