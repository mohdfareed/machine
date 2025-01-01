"""App models."""

from abc import ABC
from pathlib import Path
from typing import Callable, Optional, Protocol, TypeVar

import typer
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from app import utils

T = TypeVar("T", bound="Environment")


# MARK: Types


class ConfigFiles(BaseModel, ABC):
    """Configuration files."""


class Environment(BaseSettings, ABC):
    """Environment variables."""

    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    @classmethod
    def load(
        cls: type[T], env_file: Path, executable: Optional[utils.Executable] = None
    ) -> T:
        """Load the environment variables from file."""
        return utils.load_env(cls(), env_file, executable)


PackageSpec = tuple[type["PackageManagerProtocol"], Callable[[], None]]


# MARK: Protocols


class PackageManagerProtocol(Protocol):
    """Package manager protocol."""

    def app(self) -> typer.Typer:
        """The package manager's Typer app."""
        raise NotImplementedError

    @classmethod
    def is_supported(cls) -> bool:
        """Check if the package manager is supported."""
        raise NotImplementedError


class PluginProtocol(Protocol):
    """Plugin protocol required for registration to a machine."""

    plugin_app: typer.Typer

    def setup(self) -> None:
        """Setup the plugin."""


class MachineProtocol(Protocol):
    """Machine protocol."""

    machine_app: typer.Typer

    def setup(self) -> None:
        """Setup the machine."""


# MARK: Exceptions


class PluginException(Exception):
    """Plugin exception."""


class PackageManagerException(Exception):
    """Base exception for package manager errors."""


class MachineException(Exception):
    """Base exception for machine errors."""
