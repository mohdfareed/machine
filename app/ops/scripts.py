"""Script filtering, execution, and run tracking."""

import hashlib
import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from app.discovery import SCRIPT_SUFFIXES
from app.env import PLATFORM, is_unix, settings
from app.logging import err_console
from app.models import Failure, Platform
from app.shell import refresh_path, run

_logger = logging.getLogger(__name__)


# =============================================================================
# MARK: Script Selection
# =============================================================================


def filter_scripts(scripts: list[str]) -> list[str]:
    """Return scripts that match the current platform and are runnable."""
    return [
        s
        for s in scripts
        if (p := Path(s)).suffix.lower() in SCRIPT_SUFFIXES
        and _matches_platform(p)
        and not p.stem.startswith("_")
    ]


def _matches_platform(script: Path) -> bool:

    tags = {
        ".macos": Platform.MACOS,
        ".linux": Platform.LINUX,
        ".unix": Platform.UNIX,
        ".win": Platform.WINDOWS,
        ".wsl": Platform.WSL,
    }
    targets = [tags[suffix.lower()] for suffix in script.suffixes if suffix.lower() in tags]
    return not targets or any(PLATFORM.is_a(target) for target in targets)


# =============================================================================
# MARK: Script Pipeline
# =============================================================================


def run_scripts(
    scripts: list[str],
    env: dict[str, str] | None = None,
    owners: dict[str, str] | None = None,
) -> list[Failure]:
    """Run pre-filtered scripts, respecting `once_`/`watch_` tracking."""
    if not scripts:
        return []

    # Load tracking state before processing the script pipeline.
    state = _load_state()
    _logger.info("Scripts: %d to run", len(scripts))
    failures: list[Failure] = []

    for script in (Path(s) for s in scripts):
        tracked = script.name.startswith(("once_", "watch_"))
        module = (owners or {}).get(str(script), "?")

        # Skip tracked scripts that do not need another run.
        if tracked and script.name in state:
            if script.name.startswith("once_"):
                _logger.debug("Skip (already ran): %s", script.name)
                continue

            current_hash = hashlib.sha256(script.read_bytes()).hexdigest()[:16]
            if state[script.name].get("hash") == current_hash:
                _logger.debug("Skip (unchanged): %s", script.name)
                continue

        # Stop on initialization failure; refresh PATH after successful setup.
        fail = _execute(script, env, module)
        if fail:
            failures.append(fail)
            if script.name.startswith("init_"):
                break
        elif script.name.startswith("init_") and not settings.dry_run:
            refresh_path()

        # Record tracked script attempts.
        if tracked:
            state[script.name] = {
                "hash": hashlib.sha256(script.read_bytes()).hexdigest()[:16],
                "ran": datetime.now(UTC).isoformat(),
            }

    # Persist shared state even when an initialization failure stops the pipeline.
    _save_state(state)
    return failures


# =============================================================================
# MARK: Script Execution
# =============================================================================


def _execute(
    script: Path,
    env: dict[str, str] | None = None,
    module: str = "?",
) -> Failure | None:
    # Prepare script permissions and announce execution.
    if is_unix and not os.access(script, os.X_OK):
        os.chmod(script, 0o755)

    _logger.info("[%s] Run: %s", module, script.name)
    if not settings.debug:
        err_console.print(rf"  [dim]\[{module}][/] {script.stem}")

    if settings.dry_run:
        _logger.info("[dry-run] [%s] %s", module, script.name)
        return None

    # Select the script interpreter.
    match script.suffix.lower():
        case ".py":
            cmd = f"{sys.executable} {script}"
        case ".ps1":
            if PLATFORM.is_a(Platform.WINDOWS):
                cmd = f'powershell -ExecutionPolicy Bypass -File "{script}"'
            else:
                cmd = f'pwsh -File "{script}"'
        case _:
            cmd = str(script)

    # Stream execution output and report failures relative to the repository.
    rc = run(cmd, env=env, label=module).returncode
    if rc == 0:
        return None

    try:
        rel = script.relative_to(settings.home)
    except ValueError:
        rel = script

    _logger.error("[%s] Script failed (exit %d): %s", module, rc, rel)
    return Failure(module=module, item=str(rel), detail=f"exit {rc}")


# =============================================================================
# MARK: Script State
# =============================================================================


def _load_state() -> dict:
    if not settings.state_file.exists():
        return {}

    try:
        return json.loads(settings.state_file.read_text())
    except json.JSONDecodeError, KeyError:
        _logger.warning("Corrupted state, resetting")
        return {}


def _save_state(state: dict) -> None:
    if settings.dry_run:
        return

    settings.state_file.parent.mkdir(parents=True, exist_ok=True)
    settings.state_file.write_text(json.dumps(state, indent=2))
