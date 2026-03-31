"""Script env building, filtering, execution, and script-run tracking."""

import hashlib
import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from machine.core import PLATFORM, Platform, err_console, is_unix, run, settings
from machine.manifest import SCRIPT_SUFFIXES

logger = logging.getLogger(__name__)

_ENV_FILE = Path.home() / ".env"
_STATE_FILE = settings.app_dir / "state.json"


def build_script_env(machine_id: str, root: Path) -> dict[str, str]:
    """Build the env dict injected into every script subprocess."""
    raw: dict[str, str] = {
        "MC_HOME": str(root),
        "MC_ID": machine_id,
        "MC_PRIVATE": str(settings.app_dir / "private"),
    }

    def _parse_env(path: Path) -> None:
        if not path.is_file():
            return
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, value = line.partition("=")
            if key and _:
                raw[key.strip()] = value.strip().strip('"').strip("'")

    _parse_env(root / "machines" / machine_id / "machine.env")
    env = _resolve_env(raw)

    mc_private = env.get("MC_PRIVATE", "")
    if mc_private:
        _parse_env(Path(mc_private) / "env" / f"{machine_id}.env")
        env = _resolve_env(raw)

    return env


def write_env_file(machine_id: str, root: Path) -> None:
    """Write `~/.env` with MC_HOME and MC_ID for login shell consumption."""
    if settings.dry_run:
        logger.info("[dry-run] write %s", _ENV_FILE)
        return
    _ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    _ENV_FILE.write_text(f"MC_HOME={root}\nMC_ID={machine_id}\n")
    logger.info("Wrote %s", _ENV_FILE)


def matches_platform(script: Path) -> bool:
    """Return True if the script's platform tags match the current platform."""
    suffixes = {s.lower() for s in script.suffixes}
    tags = {".macos", ".linux", ".unix", ".win", ".wsl", ".ghcs"}

    if not (suffixes & tags):
        return True

    match PLATFORM:
        case Platform.MACOS:
            return bool(suffixes & {".macos", ".unix"})
        case Platform.LINUX:
            return bool(suffixes & {".linux", ".unix"})
        case Platform.WSL:
            return bool(suffixes & {".wsl", ".linux", ".unix"})
        case Platform.WINDOWS:
            return bool(suffixes & {".win"})
        case Platform.GHCS:
            return bool(suffixes & {".ghcs", ".linux", ".unix"})
    raise AssertionError(f"Unhandled platform: {PLATFORM}")


def filter_scripts(scripts: list[str]) -> list[str]:
    """Return scripts that match the current platform and are runnable."""
    return [
        s
        for s in scripts
        if (p := Path(s)).suffix.lower() in SCRIPT_SUFFIXES
        and matches_platform(p)
        and not p.stem.startswith("_")
    ]


def run_scripts(
    scripts: list[str],
    env: dict[str, str] | None = None,
    owners: dict[str, str] | None = None,
) -> list[tuple[str, str, str]]:
    """Run pre-filtered scripts, respecting `once_`/`watch_` tracking."""
    if not scripts:
        return []

    state = _load_state()
    logger.info("Scripts: %d to run", len(scripts))
    failures: list[tuple[str, str, str]] = []

    for script in (Path(s) for s in scripts):
        tracked = script.name.startswith(("once_", "watch_"))
        module = (owners or {}).get(str(script), "?")

        if tracked and script.name in state:
            if script.name.startswith("once_"):
                logger.debug("Skip (already ran): %s", script.name)
                continue
            current_hash = hashlib.sha256(script.read_bytes()).hexdigest()[:16]
            if state[script.name].get("hash") == current_hash:
                logger.debug("Skip (unchanged): %s", script.name)
                continue

        fail = _execute(script, env, module)
        if fail:
            failures.append(fail)

        if tracked:
            state[script.name] = {
                "hash": hashlib.sha256(script.read_bytes()).hexdigest()[:16],
                "ran": datetime.now(UTC).isoformat(),
            }

    _save_state(state)
    return failures


def _resolve_env(raw: dict[str, str]) -> dict[str, str]:
    """Expand `$VAR` references in env values until stable."""
    env = {key: os.path.expandvars(value) for key, value in raw.items()}
    for _ in range(len(env)):
        changed = False
        for key, value in env.items():
            new = value
            for env_key, env_value in env.items():
                new = new.replace(f"${env_key}", env_value)
            if new != value:
                env[key] = new
                changed = True
        if not changed:
            break
    return env


def _execute(
    script: Path,
    env: dict[str, str] | None = None,
    module: str = "?",
) -> tuple[str, str, str] | None:
    """Run a script, teeing output to terminal and log. Returns Failure on error."""
    if is_unix and not os.access(script, os.X_OK):
        os.chmod(script, 0o755)

    logger.info("[%s] run: %s", module, script.name)
    if not settings.debug:
        err_console.print(rf"  [dim]\[{module}][/] {script.stem}")

    if settings.dry_run:
        logger.info("[dry-run] [%s] %s", module, script.name)
        return None

    match script.suffix.lower():
        case ".py":
            cmd = f"{sys.executable} {script}"
        case ".ps1":
            if PLATFORM == Platform.WINDOWS:
                cmd = f'powershell -ExecutionPolicy Bypass -File "{script}"'
            else:
                cmd = f'pwsh -File "{script}"'
        case _:
            cmd = str(script)

    rc = run(cmd, env=env, label=module)
    if rc == 0:
        return None

    try:
        rel = script.relative_to(settings.home)
    except ValueError:
        rel = script
    logger.error("[%s] script failed (exit %d): %s", module, rc, rel)
    return (module, str(rel), f"exit {rc}")


def _load_state() -> dict:
    if _STATE_FILE.exists():
        try:
            return json.loads(_STATE_FILE.read_text())
        except json.JSONDecodeError, KeyError:
            logger.warning("Corrupted state, resetting")
    return {}


def _save_state(state: dict) -> None:
    if settings.dry_run:
        return
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(json.dumps(state, indent=2))
