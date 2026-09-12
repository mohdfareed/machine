"""Runtime settings, platform detection, and shared machine environment."""

import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from app.models import Platform, Settings

_ENV_FILE = Path.home() / ".env"
_ENV_REFERENCE = re.compile(
    r"\$(?:{(?P<braced>[A-Za-z_][A-Za-z0-9_]*)}|(?P<plain>[A-Za-z_][A-Za-z0-9_]*))"
)
_PWSH_MODULES_ROOT = str(Path(__file__).parent / "pwsh")
_logger = logging.getLogger(__name__)

# Settings singleton
settings = Settings()
"""Runtime settings singleton."""


# =============================================================================
# MARK: Platform
# =============================================================================


PLATFORM: Platform
"""Current platform, detected at import time."""

match sys.platform:
    case _ if shutil.which("wslinfo"):
        PLATFORM = Platform.WSL
    case _platform if _platform.startswith("darwin"):
        PLATFORM = Platform.MACOS
    case _platform if _platform.startswith("linux"):
        PLATFORM = Platform.LINUX
    case _platform if _platform.startswith("win"):
        PLATFORM = Platform.WINDOWS
    case _:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")

is_macos = PLATFORM.is_a(Platform.MACOS)
is_linux = PLATFORM.is_a(Platform.LINUX)
is_windows = PLATFORM.is_a(Platform.WINDOWS)
is_wsl = PLATFORM.is_a(Platform.WSL)
is_unix = PLATFORM.is_a(Platform.UNIX)


# =============================================================================
# MARK: Environment
# =============================================================================


def build_env(machine_id: str, root: Path) -> dict[str, str]:
    """Build machine variables and shell-specific additions for subprocesses."""
    # Seed the machine identity and default private directory.
    env: dict[str, str] = {
        "MC_HOME": str(root),
        "MC_ID": machine_id,
        "MC_PRIVATE": str(settings.app_dir / "private"),
    }

    # Resolve machine and private env files.
    env = _resolve_env(root / "machines" / machine_id / "machine.env", env)
    if mc_private := env.get("MC_PRIVATE", ""):
        env = _resolve_env(Path(mc_private) / "env" / f"{machine_id}.env", env)

    # Add bundled PowerShell modules while preserving the existing module path.
    shell = "powershell" if PLATFORM.is_a(Platform.WINDOWS) else "pwsh"
    if shutil.which(shell):
        module_path = _get_pwsh_module_path(shell, env)
        env["PSModulePath"] = os.pathsep.join(filter(None, [_PWSH_MODULES_ROOT, module_path]))

    return env


def write_env_file(machine_id: str, root: Path) -> None:
    """Write MC_HOME and MC_ID to ~/.env for login shells."""
    if not settings.dry_run:
        _ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
        _ENV_FILE.write_text(f"MC_HOME={root}\nMC_ID={machine_id}\n")
    _logger.info("Wrote %s", _ENV_FILE)


# =============================================================================
# MARK: Helpers
# =============================================================================


def _resolve_env(path: Path, raw: dict[str, str]) -> dict[str, str]:
    env = dict(raw)

    # Overlay file values before expansion so references declared in the same
    # file are resolved before callers use them to locate another env file.
    if path.is_file():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            key, separator, value = line.partition("=")
            if not key or not separator:
                continue
            env[key.strip()] = value.strip().strip('"').strip("'")

    # Expand env references in values until no changes occur.
    for _ in range(len(env)):
        changed = False
        context = {**os.environ, **env}

        for key, value in env.items():
            new = _ENV_REFERENCE.sub(
                lambda match: context.get(
                    match.group("braced") or match.group("plain"), match.group(0)
                ),
                value,
            )

            if new != value:
                env[key] = new
                changed = True

        if not changed:
            break

    return env


def _get_pwsh_module_path(shell: str, env: dict[str, str]) -> str:
    module_path = env.get("PSModulePath", os.environ.get("PSModulePath"))
    if module_path is not None:
        return module_path

    # Let PowerShell resolve its defaults before adding our module directory.
    return subprocess.check_output(
        [
            shell,
            "-NoProfile",
            "-Command",
            "[Console]::OutputEncoding = [Text.UTF8Encoding]::new(); $env:PSModulePath",
        ],
        env={**os.environ, **env},
        encoding="utf-8",
    ).strip()
