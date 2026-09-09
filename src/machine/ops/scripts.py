"""Script env building, filtering, execution, and script-run tracking."""

import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from machine.core import PLATFORM, Platform, err_console, is_unix, run, settings
from machine.manifest import SCRIPT_SUFFIXES
from machine.ops.packages import refresh_path

logger = logging.getLogger(__name__)

_ENV_FILE = Path.home() / ".env"
_ENV_REFERENCE = re.compile(
    r"\$(?:{(?P<braced>[A-Za-z_][A-Za-z0-9_]*)}|(?P<plain>[A-Za-z_][A-Za-z0-9_]*))"
)


def build_script_env(machine_id: str, root: Path) -> dict[str, str]:
    """Build the env dict injected into every script subprocess."""
    env: dict[str, str] = {
        "MC_HOME": str(root),
        "MC_ID": machine_id,
        "MC_PRIVATE": str(settings.app_dir / "private"),
    }

    # Resolve machine and private env files.
    env = _resolve_env(root / "machines" / machine_id / "machine.env", env)
    if mc_private := env.get("MC_PRIVATE", ""):
        env = _resolve_env(Path(mc_private) / "env" / f"{machine_id}.env", env)

    # Shell-specific additions share the same environment as the machine variables.
    shell = "powershell" if PLATFORM.is_a(Platform.WINDOWS) else "pwsh"
    if shutil.which(shell):
        module_root = str(Path(__file__).parents[1] / "powershell")
        module_path = _get_pwsh_module_path(shell, env)
        env["PSModulePath"] = os.pathsep.join(filter(None, [module_root, module_path]))

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
    tags = {
        ".macos": Platform.MACOS,
        ".linux": Platform.LINUX,
        ".unix": Platform.UNIX,
        ".win": Platform.WINDOWS,
        ".wsl": Platform.WSL,
    }
    targets = [tags[suffix.lower()] for suffix in script.suffixes if suffix.lower() in tags]
    return not targets or any(PLATFORM.is_a(target) for target in targets)


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
            if script.name.startswith("init_"):
                break
        elif script.name.startswith("init_") and not settings.dry_run:
            refresh_path()

        if tracked:
            state[script.name] = {
                "hash": hashlib.sha256(script.read_bytes()).hexdigest()[:16],
                "ran": datetime.now(UTC).isoformat(),
            }

    _save_state(state)
    return failures


def _resolve_env(path: Path, raw: dict[str, str]) -> dict[str, str]:
    env = dict(raw)

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

    # No env file to load, return the resolved env.
    if not path.is_file():
        return env

    # Load env file. Values are resolved against the current env.
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        key, _, value = line.partition("=")
        if key and _:
            env[key.strip()] = value.strip().strip('"').strip("'")

    return env


def _get_pwsh_module_path(shell: str, env: dict[str, str]) -> str:
    """Return the PSModulePath as resolved by PowerShell."""
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
            if PLATFORM.is_a(Platform.WINDOWS):
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
    if settings.state_file.exists():
        try:
            return json.loads(settings.state_file.read_text())
        except json.JSONDecodeError, KeyError:
            logger.warning("Corrupted state, resetting")
    return {}


def _save_state(state: dict) -> None:
    if settings.dry_run:
        return
    settings.state_file.parent.mkdir(parents=True, exist_ok=True)
    settings.state_file.write_text(json.dumps(state, indent=2))
