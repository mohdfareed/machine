"""Platform detection, settings, logging, and shell execution."""

import logging
import os
import shutil
import subprocess
import sys
from collections.abc import Generator
from contextlib import contextmanager
from enum import StrEnum
from importlib.metadata import metadata
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import ClassVar

import typer
from rich.console import Console
from rich.logging import RichHandler

# MARK: Platform


class Platform(StrEnum):
    """Supported platforms."""

    MACOS = "macos"
    LINUX = "linux"
    WINDOWS = "windows"
    WSL = "wsl"
    GHCS = "ghcs"


def _detect() -> Platform:
    if os.environ.get("CODESPACES"):
        return Platform.GHCS
    if shutil.which("wslinfo"):
        return Platform.WSL
    match sys.platform:
        case p if p.startswith("darwin"):
            return Platform.MACOS
        case p if p.startswith("linux"):
            return Platform.LINUX
        case p if p.startswith("win"):
            return Platform.WINDOWS
        case _:
            raise RuntimeError(f"Unsupported platform: {sys.platform}")


PLATFORM = _detect()
"""Current platform, detected at import time."""

is_macos = PLATFORM == Platform.MACOS
is_linux = PLATFORM in {Platform.LINUX, Platform.WSL, Platform.GHCS}
is_windows = PLATFORM == Platform.WINDOWS
is_wsl = PLATFORM == Platform.WSL
is_unix = not is_windows


# MARK: Settings

_meta = metadata("machine")
# __file__ = src/machine/core.py → parents[2] = repo root
_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings:
    """Mutable runtime settings singleton."""

    name: ClassVar[str] = _meta["Name"]
    version: ClassVar[str] = _meta["Version"]
    description: ClassVar[str] = _meta["Summary"]
    app_dir: ClassVar[Path] = Path(typer.get_app_dir("mc"))

    debug: bool = False
    dry_run: bool = False
    home: Path = _REPO_ROOT


settings = Settings()
"""Runtime settings singleton."""


# MARK: Console

console = Console()
err_console = Console(stderr=True)


# MARK: Logging

_logger = logging.getLogger(__name__)
_console_handler: logging.Handler | None = None


def setup_console_logging() -> None:
    """Configure rich console logging."""
    global _console_handler
    level = logging.DEBUG if settings.debug else logging.INFO
    handler = RichHandler(
        level=level,
        console=err_console,
        show_time=settings.debug,
        show_path=settings.debug,
        rich_tracebacks=True,
        markup=True,
        keywords=[],
    )
    handler.setFormatter(logging.Formatter("[dim]%(name)s:[/] %(message)s"))
    logging.root.setLevel(level)
    logging.root.addHandler(handler)
    _console_handler = handler


@contextmanager
def mute_console_logging() -> Generator[None]:
    """Temporarily suppress console log output (file log unaffected)."""
    if _console_handler:
        _console_handler.setLevel(logging.CRITICAL + 1)
    try:
        yield
    finally:
        if _console_handler:
            level = logging.DEBUG if settings.debug else logging.INFO
            _console_handler.setLevel(level)


def setup_file_logging() -> None:
    """Configure rotating file logging."""
    log_file = settings.app_dir / "mc.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=3)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)-8s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    handler.setLevel(logging.DEBUG)
    logging.root.addHandler(handler)

    # Separator for new invocations
    args = " ".join(sys.argv[1:]) or "(no args)"
    _logger.info("=" * 60)
    _logger.info("mc %s", args)
    _logger.info("=" * 60)


# MARK: Shell


def run(
    cmd: str,
    *,
    check: bool = True,
    capture: bool = False,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a shell command. Skipped (logged) in dry-run mode.

    ``env`` is merged on top of the current process environment, so
    scripts inherit PATH and other system vars plus any injected keys.
    """
    _logger.debug("$ %s", cmd)

    if settings.dry_run:
        _logger.info("[dry-run] %s", cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    merged_env = {**os.environ, **(env or {})}
    exe = shutil.which("powershell.exe") if is_windows else None
    return subprocess.run(
        cmd,
        shell=True,
        check=check,
        executable=exe,
        text=True,
        capture_output=capture,
        env=merged_env,
    )
