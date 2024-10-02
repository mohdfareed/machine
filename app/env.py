"""Machine environment models."""

import os
import shutil
import subprocess
from abc import ABC
from pathlib import Path
from typing import Optional, Union

import pydantic

from app.config import Config
from app.utils import SupportedShells


class Environment(Config, ABC):
    """Environment variables."""

    def load(self, env_file: Path, shell: SupportedShells):
        """Load the environment variables from a shell file."""

        for name in self.model_fields:
            if value := load_var_var(name, env_file, shell):
                setattr(self, name, type(getattr(self, name))(value))


class Machine(Environment):
    """Machine environment variables."""

    MACHINE: Path = Path.home() / ".machine"
    PRIVATE_ENV: Optional[Path] = None
    SSH_KEYS: Optional[Path] = None


class Windows(Environment):
    """Windows environment variables."""

    LOCALAPPDATA: Path = pydantic.Field(
        default_factory=lambda: Path(os.environ["LOCALAPPDATA"]),
    )
    APPDATA: Path = pydantic.Field(
        default_factory=lambda: Path(os.environ["APPDATA"]),
    )


class Unix(Environment):
    """Unix environment variables."""

    XDG_CONFIG_HOME: Path = Path.home() / ".config"
    XDG_DATA_HOME: Path = Path().home() / ".local" / "share"
    COMPLETIONS_PATH: Optional[Path] = None


def load_var_var(name: str, env_file: Path, shell: SupportedShells) -> Union[str, None]:
    """Load a variable from a shell file."""
    if not env_file.exists(follow_symlinks=True):
        raise FileNotFoundError(f"Environment file not found: {env_file}")

    if shell in ("pwsh", "powershell"):
        cmd = f". {env_file}; Write-Output $env:{name};"
    else:
        cmd = f'source "{env_file}" && echo ${name}'

    result = subprocess.run(
        cmd,
        executable=shutil.which(shell),
        capture_output=True,
        text=True,
        check=True,
        shell=True,
    )

    output = result.stdout.strip()
    return output if output else None
