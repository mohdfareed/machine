"""Script discovery and execution."""

import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from machine.config import app_settings
from machine.platform import PLATFORM, Platform, is_unix
from machine.shell import run

logger = logging.getLogger(__name__)

STATE_FILE = Path("~/.local/state/machine/scripts.json").expanduser()


def run_scripts(script_dir: Path) -> None:
    """Discover and run platform-matching scripts from a directory."""
    if not script_dir.exists():
        return

    scripts = sorted(
        s
        for s in script_dir.iterdir()
        if s.is_file() and _runnable(s) and _matches_platform(s)
    )
    if not scripts:
        return

    state = _load_state()
    logger.info("Scripts: %d from %s/", len(scripts), script_dir.name)

    for script in scripts:
        if _is_tracked(script) and not _should_run(script, state):
            logger.debug("Skip: %s", script.name)
            continue
        _execute(script)
        if _is_tracked(script):
            _mark_run(script, state)

    _save_state(state)


# MARK: Filtering


def _runnable(path: Path) -> bool:
    return path.suffix.lower() in {".sh", ".py", ".ps1"}


def _matches_platform(script: Path) -> bool:
    """Check platform suffixes in the filename."""
    suffixes = {s.lower() for s in script.suffixes}
    tags = {".macos", ".linux", ".unix", ".win", ".wsl", ".codespaces"}

    if not (suffixes & tags):
        return True  # no tag = all platforms

    match PLATFORM:
        case Platform.MACOS:
            return bool(suffixes & {".macos", ".unix"})
        case Platform.LINUX:
            return bool(suffixes & {".linux", ".unix"})
        case Platform.WSL:
            return bool(suffixes & {".wsl", ".linux", ".unix"})
        case Platform.WINDOWS:
            return bool(suffixes & {".win"})
        case Platform.CODESPACES:
            return bool(suffixes & {".codespaces", ".linux", ".unix"})
    return False


# MARK: Execution


def _execute(script: Path) -> None:
    if is_unix and not os.access(script, os.X_OK):
        os.chmod(script, 0o755)

    logger.info("Run: %s", script.name)
    match script.suffix.lower():
        case ".py":
            run(f"{sys.executable} {script}", check=False)
        case ".ps1":
            if PLATFORM == Platform.WINDOWS:
                run(
                    f'powershell -ExecutionPolicy Bypass -File "{script}"',
                    check=False,
                )
            else:
                run(f'pwsh -File "{script}"', check=False)
        case _:
            run(str(script), check=False)


# MARK: State Tracking


def _is_tracked(script: Path) -> bool:
    return script.name.startswith(("once_", "onchange_"))


def _should_run(script: Path, state: dict) -> bool:
    key = script.name
    if key not in state:
        return True
    if script.name.startswith("onchange_"):
        return state[key].get("hash") != _hash(script)
    return False  # once_ already ran


def _mark_run(script: Path, state: dict) -> None:
    state[script.name] = {
        "hash": _hash(script),
        "ran": datetime.now(timezone.utc).isoformat(),
    }


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError, KeyError:
            logger.warning("Corrupted state, resetting")
    return {}


def _save_state(state: dict) -> None:
    if app_settings.dry_run:
        return
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))
