"""App models."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol, TypedDict, TypeVar

import typer
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

T = TypeVar("T", bound="BaseEnvironment")


class BaseConfig(BaseModel, ABC):
    """Configuration files."""


class BaseEnvironment(BaseSettings, ABC):
    """Environment variables."""

    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    @abstractmethod
    def load(self: T, env: Path) -> T:
        """Load environment variables from a file."""


class PluginProtocol(Protocol):  # pylint: disable=too-few-public-methods
    """Plugin protocol required to register it to a machine."""

    plugin_app: typer.Typer


class MachineProtocol(Protocol):  # pylint: disable=too-few-public-methods
    """Machine protocol required to register it to the app."""

    machine_app: typer.Typer


class PluginException(Exception):
    """Plugin exception."""


class PackageManagerException(Exception):
    """Base exception for package manager errors."""


class PackageSpec(TypedDict):
    """Package installation specification."""
