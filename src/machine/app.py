"""Dotfile deployment, package installation, and script execution."""

import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

from machine.core import PLATFORM, Platform, err_console, is_unix, run, settings
from machine.manifest import SCRIPT_SUFFIXES, FileMapping, Module, Package

logger = logging.getLogger(__name__)

# Structured failure record for end-of-run summaries
Failure = tuple[str, str, str]  # (module, item, detail)

_STATE_FILE = settings.app_dir / "state.json"
_MACHINE_FILE = settings.app_dir / "machine.txt"
_MANAGERS = ("brew", "apt", "snap", "winget", "scoop", "mas")

_INSTALL_CMD = {
    "brew": "brew install {}",
    "apt": "sudo apt install -y {}",
    "snap": "sudo snap install {}",
    "winget": "winget install --accept-source-agreements --accept-package-agreements {}",
    "scoop": "scoop install {}",
    "mas": "mas install {}",
}


# MARK: Sudo

_sudo_keepalive: threading.Event | None = None


def cache_sudo() -> None:
    """Prompt for sudo once and keep credentials alive in the background."""
    global _sudo_keepalive

    if not is_unix or settings.dry_run or _sudo_keepalive is not None:
        return

    # Initial prompt — the only interactive one.
    rc = subprocess.call(["sudo", "-v"], stdin=sys.stdin)
    if rc != 0:
        logger.warning("sudo -v failed (exit %d); scripts may re-prompt", rc)
        return

    stop = threading.Event()
    _sudo_keepalive = stop

    def _keepalive() -> None:
        while not stop.wait(60):
            subprocess.call(["sudo", "-v"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    t = threading.Thread(target=_keepalive, daemon=True)
    t.start()


# MARK: Validation


def validate(
    modules: list[Module],
    machine_id: str,
) -> list[str]:
    """Validate resolved modules. Returns a list of errors."""
    errors: list[str] = []

    for mod in modules:
        for fm in mod.files:
            if not Path(fm.source).exists():
                errors.append(f"Module '{mod.name}' file source missing: {fm.source}")
        for script in mod.scripts:
            if not Path(script).exists():
                errors.append(f"Module '{mod.name}' script missing: {script}")

    return errors


# MARK: Files


def deploy_files(
    files: list[FileMapping],
    owners: dict[str, str] | None = None,
) -> tuple[int, list[Failure]]:
    """Symlink all file mappings. Returns (count created, failures)."""
    created = 0
    failures: list[Failure] = []
    for fm in files:
        src = Path(fm.source)
        tgt = Path(os.path.expandvars(fm.target)).expanduser()
        module = (owners or {}).get(fm.source, "?")
        if not src.exists():
            logger.warning("[%s] source not found: %s", module, src)
            failures.append((module, str(src), "source not found"))
        elif _symlink(src, tgt):
            created += 1
    return created, failures


def _symlink(source: Path, target: Path) -> bool:
    """Create or update a symlink. Returns True if changed."""
    if settings.dry_run:
        if target.is_symlink() and target.resolve() == source.resolve():
            return False
        logger.info("[dry-run] link %s → %s", target, source)
        return True

    target.parent.mkdir(parents=True, exist_ok=True)

    if target.is_symlink():
        if target.resolve() == source.resolve():
            logger.debug("OK: %s", target)
            return False
        logger.info("Update: %s → %s", target, source)
        target.unlink()
    elif target.exists():
        backup = target.with_suffix(target.suffix + ".backup")
        logger.info("Backup: %s → %s", target, backup)
        target.rename(backup)
    else:
        logger.info("Link: %s → %s", target, source)

    target.symlink_to(source)
    return True


# MARK: Packages


def install_packages(
    packages: list[Package],
    owners: dict[str, str] | None = None,
) -> list[Failure]:
    """Install packages using available managers. Returns list of failures."""
    if not packages:
        return []

    managers = {m for m in _MANAGERS if shutil.which(m)}
    logger.info("Managers: %s", ", ".join(sorted(managers)) or "none")

    state = _load_state()
    installed: set[str] = set(state.get("packages", []))

    failures: list[Failure] = []
    skipped = 0
    for pkg in packages:
        if pkg.name in installed:
            logger.debug("Skip (installed): %s", pkg.name)
            skipped += 1
            continue
        module = (owners or {}).get(pkg.name, "?")
        fail = _install(pkg, managers, module)
        if fail:
            failures.append(fail)
        else:
            installed.add(pkg.name)

    state["packages"] = sorted(installed)
    _save_state(state)

    if skipped:
        logger.info("Skipped %d already-installed package(s)", skipped)
    return failures


def _install(
    pkg: Package,
    managers: set[str],
    module: str = "?",
) -> Failure | None:
    """Try to install a package. Returns a Failure on error, else None."""
    for mgr in _MANAGERS:
        val = getattr(pkg, mgr, None)
        if val is None or mgr not in managers:
            continue
        cmd = _INSTALL_CMD[mgr].format(val)
        logger.info("[%s] %s: %s", module, pkg.name, mgr)
        rc = run(cmd, label=module)
        if rc != 0:
            logger.error(
                "[%s] failed to install %s via %s (exit %d): %s", module, pkg.name, mgr, rc, cmd
            )
            return (module, pkg.name, f"{mgr} exit {rc}")
        return None

    if pkg.script:
        logger.info("[%s] %s: script", module, pkg.name)
        rc = run(pkg.script, label=module)
        if rc != 0:
            logger.error(
                "[%s] failed to install %s via script (exit %d): %s",
                module,
                pkg.name,
                rc,
                pkg.script,
            )
            return (module, pkg.name, f"script exit {rc}")
        return None

    logger.warning("[%s] no manager for: %s", module, pkg.name)
    return None


# MARK: Scripts


_ENV_FILE = Path.home() / ".env"


def build_script_env(
    machine_id: str,
    root: Path,
) -> dict[str, str]:
    """Build the env dict injected into every script subprocess.

    Three-tier sourcing:
      1. MC_HOME + MC_ID (always present)
      2. ``machines/<id>/machine.env`` — committed config vars
      3. ``$MC_PRIVATE/env/$MC_ID.env`` — machine secrets (if MC_PRIVATE set)

    Values may reference earlier vars with ``$VAR``; all references are
    resolved iteratively.
    """
    raw: dict[str, str] = {
        "MC_HOME": str(root),
        "MC_ID": machine_id,
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
                value = value.strip().strip('"').strip("'")
                raw[key.strip()] = value

    # Tier 2: committed machine config vars
    _parse_env(root / "machines" / machine_id / "machine.env")

    # Resolve $VAR references so MC_PRIVATE is available for tier 3
    env = _resolve_env(raw)

    # Tier 3: private secrets
    mc_private = env.get("MC_PRIVATE", "")
    if mc_private:
        _parse_env(Path(mc_private) / "env" / f"{machine_id}.env")
        env = _resolve_env(raw)

    return env


def _resolve_env(raw: dict[str, str]) -> dict[str, str]:
    """Expand ``$VAR`` references in env values until stable."""
    env = {k: os.path.expandvars(v) for k, v in raw.items()}
    for _ in range(len(env)):
        changed = False
        for key, value in env.items():
            new = value
            for k, v in env.items():
                new = new.replace(f"${k}", v)
            if new != value:
                env[key] = new
                changed = True
        if not changed:
            break
    return env


def write_env_file(machine_id: str, root: Path) -> None:
    """Write ``~/.env`` with MC_HOME and MC_ID for login shell consumption."""
    if settings.dry_run:
        logger.info("[dry-run] write %s", _ENV_FILE)
        return
    content = f"MC_HOME={root}\nMC_ID={machine_id}\n"
    _ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    _ENV_FILE.write_text(content)
    logger.info("Wrote %s", _ENV_FILE)


def matches_platform(script: Path) -> bool:
    """Return True if the script's platform tags match the current platform."""
    suffixes = {s.lower() for s in script.suffixes}
    tags = {".macos", ".linux", ".unix", ".win", ".wsl", ".ghcs"}

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
        case Platform.GHCS:
            return bool(suffixes & {".ghcs", ".linux", ".unix"})
    raise AssertionError(f"Unhandled platform: {PLATFORM}")


def filter_scripts(scripts: list[str]) -> list[str]:
    """Return scripts that match the current platform and are runnable.

    Scripts whose stem starts with ``_`` are helpers intended to be
    sourced by other scripts — they are never executed directly.
    """
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
) -> list[Failure]:
    """Run pre-filtered scripts, respecting ``once_``/``watch_`` tracking."""
    if not scripts:
        return []

    state = _load_state()
    logger.info("Scripts: %d to run", len(scripts))
    failures: list[Failure] = []

    for script in (Path(s) for s in scripts):
        tracked = script.name.startswith(("once_", "watch_"))
        module = (owners or {}).get(str(script), "?")

        # Check tracking: once_ run once, watch_ re-run on file change
        if tracked and script.name in state:
            if script.name.startswith("once_"):
                logger.debug("Skip (already ran): %s", script.name)
                continue
            cur_hash = hashlib.sha256(script.read_bytes()).hexdigest()[:16]
            if state[script.name].get("hash") == cur_hash:
                logger.debug("Skip (unchanged): %s", script.name)
                continue

        fail = _execute(script, env, module)
        if fail:
            failures.append(fail)

        if tracked:
            state[script.name] = {
                "hash": hashlib.sha256(script.read_bytes()).hexdigest()[:16],
                "ran": datetime.now(timezone.utc).isoformat(),
            }

    _save_state(state)
    return failures


def _execute(
    script: Path,
    env: dict[str, str] | None = None,
    module: str = "?",
) -> Failure | None:
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
    if rc != 0:
        # Show path relative to repo root for readability
        try:
            rel = script.relative_to(settings.home)
        except ValueError:
            rel = script
        logger.error("[%s] script failed (exit %d): %s", module, rc, rel)
        return (module, str(rel), f"exit {rc}")
    return None


# MARK: Machine


def get_current_machine() -> str | None:
    """Return the last-used machine ID, or None if not set."""
    return _MACHINE_FILE.read_text().strip() if _MACHINE_FILE.exists() else None


def save_current_machine(machine_id: str) -> None:
    """Persist the current machine ID."""
    _MACHINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _MACHINE_FILE.write_text(machine_id)


# MARK: State


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
