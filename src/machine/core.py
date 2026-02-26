"""Platform detection, settings, logging, and shell execution."""

import logging
import os
import re
import shutil
import subprocess
import sys
from enum import StrEnum
from importlib.metadata import metadata
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import ClassVar

import typer
from rich.console import Console
from rich.logging import RichHandler

# MARK: Settings

_meta = metadata("machine")
# __file__ = src/machine/core.py → parents[2] = repo root
_REPO_ROOT = Path(__file__).resolve().parents[2]

# Strip ANSI/DEC escape sequences for log-file output
_ANSI_RE = re.compile(r"\x1b(?:\[[0-9;?]*[A-Za-z]|\][^\x07]*\x07|\([A-Z])")


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


# MARK: Platform


class Platform(StrEnum):
    """Supported platforms."""

    MACOS = "macos"
    LINUX = "linux"
    WINDOWS = "windows"
    WSL = "wsl"
    GHCS = "ghcs"


def _detect_platform() -> Platform:
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


PLATFORM = _detect_platform()
"""Current platform, detected at import time."""

is_macos = PLATFORM == Platform.MACOS
is_linux = PLATFORM in {Platform.LINUX, Platform.WSL, Platform.GHCS}
is_windows = PLATFORM == Platform.WINDOWS
is_wsl = PLATFORM == Platform.WSL
is_unix = not is_windows


# MARK: Console


console = Console()
err_console = Console(stderr=True)


# MARK: Logging


_logger = logging.getLogger(__name__)
_console_handler: logging.Handler | None = None

# Output logger for tee'd subprocess lines — file only, never to console
_output_logger = logging.getLogger(__name__ + ".output")
_output_logger.propagate = False


def setup_console_logging() -> None:
    """Configure rich console logging."""
    global _console_handler
    level = logging.DEBUG if settings.debug else logging.WARNING
    handler = RichHandler(
        level=level,
        console=err_console,
        show_time=settings.debug,
        show_path=settings.debug,
        rich_tracebacks=settings.debug,
        markup=False,
        keywords=[],
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    logging.root.setLevel(logging.DEBUG)  # file handler always gets DEBUG
    logging.root.addHandler(handler)
    _console_handler = handler


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
    _output_logger.addHandler(handler)  # tee output goes to file only

    # Separator for new invocations
    _logger.debug("=" * 60)
    _logger.debug("mc %s", " ".join(sys.argv[1:]) or "(no args)")
    _logger.debug("=" * 60)


# MARK: Shell


def _short(cmd: str) -> str:
    """Replace absolute repo paths with relative ones for cleaner logs."""
    return cmd.replace(str(_REPO_ROOT) + os.sep, "").replace(str(_REPO_ROOT), ".")


def run(
    cmd: str,
    *,
    check: bool = True,
    capture: bool = False,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a shell command. Skipped (logged) in dry-run mode."""
    _logger.debug("$ %s", _short(cmd))

    if settings.dry_run:
        _logger.info("[dry-run] %s", _short(cmd))
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


def tee_run(
    cmd: str,
    *,
    env: dict[str, str] | None = None,
    label: str = "",
) -> int:
    """Run a shell command, streaming output to terminal and log file."""
    _logger.debug("$ %s", _short(cmd))

    if settings.dry_run:
        _logger.info("[dry-run] %s", _short(cmd))
        return 0

    merged_env = {**os.environ, **(env or {})}

    if is_unix:
        rc, collected = _tee_pty(cmd, merged_env)
    else:
        rc, collected = _tee_pipe(cmd, merged_env)

    # Log captured output line by line (strip ANSI escapes for the log file)
    prefix = f"[{label}] " if label else ""
    for line in collected.decode(errors="replace").splitlines():
        stripped = _ANSI_RE.sub("", line).rstrip()
        if stripped:
            _output_logger.debug("%s| %s", prefix, stripped)

    return rc


def _tee_pty(cmd: str, env: dict[str, str]) -> tuple[int, bytearray]:
    """Run *cmd* inside a pty, teeing output to stdout. Unix only."""
    import pty
    import select

    primary, replica = pty.openpty()
    proc = subprocess.Popen(
        cmd,
        shell=True,
        env=env,
        stdin=sys.stdin,
        stdout=replica,
        stderr=replica,
    )
    os.close(replica)  # parent doesn't write to the replica side

    collected = bytearray()
    try:
        while True:
            ready, _, _ = select.select([primary], [], [], 0.1)
            if ready:
                try:
                    chunk = os.read(primary, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                sys.stdout.buffer.write(chunk)
                sys.stdout.buffer.flush()
                collected.extend(chunk)
            elif proc.poll() is not None:
                # Process exited; drain remaining output
                while True:
                    try:
                        chunk = os.read(primary, 4096)
                    except OSError:
                        break
                    if not chunk:
                        break
                    sys.stdout.buffer.write(chunk)
                    sys.stdout.buffer.flush()
                    collected.extend(chunk)
                break
    finally:
        os.close(primary)

    proc.wait()
    return proc.returncode, collected


def _tee_pipe(cmd: str, env: dict[str, str]) -> tuple[int, bytearray]:
    """Fallback tee using pipes (no color preservation). Windows."""
    exe = shutil.which("powershell.exe") if is_windows else None
    proc = subprocess.Popen(
        cmd,
        shell=True,
        executable=exe,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert proc.stdout is not None

    collected = bytearray()
    while True:
        chunk = os.read(proc.stdout.fileno(), 4096)
        if not chunk:
            break
        sys.stdout.buffer.write(chunk)
        sys.stdout.buffer.flush()
        collected.extend(chunk)

    proc.wait()
    return proc.returncode, collected
