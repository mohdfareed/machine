"""Dotfile deployment, package installation, and script execution."""

import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from machine.core import PLATFORM, Platform, is_unix, run, settings
from machine.manifest import FileMapping, MachineManifest, Module, Package

logger = logging.getLogger(__name__)

_STATE_FILE = settings.app_dir / "state.json"
_MACHINE_FILE = settings.app_dir / "machine.txt"
_SCRIPT_SUFFIXES = {".sh", ".py", ".ps1"}
_MANAGERS = ("brew", "apt", "snap", "winget", "scoop", "mas")

_INSTALL_CMD = {
    "brew": "brew install {}",
    "apt": "sudo apt install -y {}",
    "snap": "sudo snap install {}",
    "winget": "winget install --accept-source-agreements --accept-package-agreements {}",
    "scoop": "scoop install {}",
    "mas": "mas install {}",
}


# MARK: Validation


def validate(
    modules: list[Module],
    manifest_env: dict[str, str],
    machine_id: str,
) -> list[str]:
    """Validate resolved modules against the manifest. Returns a list of errors."""
    errors: list[str] = []
    provided = {"MC_HOME", "MC_ID", "MC_NAME"} | manifest_env.keys()

    for mod in modules:
        for var in mod.required_env:
            if var not in provided:
                errors.append(
                    f"Module '{mod.name}' requires env '{var}' "
                    f"but '{machine_id}' does not provide it"
                )
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
    on_advance: Callable[[str], None] | None = None,
) -> int:
    """Symlink all file mappings. Returns count created/updated."""
    created = 0
    for fm in files:
        src = Path(fm.source)
        tgt = Path(os.path.expandvars(fm.target)).expanduser()
        if not src.exists():
            logger.warning("Source not found: %s", src)
        elif _symlink(src, tgt):
            created += 1
        if on_advance:
            on_advance(tgt.name)
    return created


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
    on_before: Callable[[str], None] | None = None,
    on_after: Callable[[str], None] | None = None,
) -> None:
    """Install packages using available managers."""
    if not packages:
        return

    managers = {m for m in _MANAGERS if shutil.which(m)}
    logger.info("Managers: %s", ", ".join(sorted(managers)) or "none")

    for pkg in packages:
        if on_before:
            on_before(pkg.name)
        _install(pkg, managers)
        if on_after:
            on_after(pkg.name)


def _install(pkg: Package, managers: set[str]) -> None:
    """Try to install a package via the first available manager."""
    for mgr in _MANAGERS:
        val = getattr(pkg, mgr, None)
        if val is None or mgr not in managers:
            continue
        logger.info("%s: %s", pkg.name, mgr)
        result = run(_INSTALL_CMD[mgr].format(val), check=False)
        if result.returncode != 0:
            logger.error("Failed to install %s (exit %d)", pkg.name, result.returncode)
        return

    if pkg.script:
        logger.info("%s: script", pkg.name)
        result = run(pkg.script, check=False)
        if result.returncode != 0:
            logger.error("Failed to install %s (exit %d)", pkg.name, result.returncode)
        return

    logger.warning("No manager for: %s", pkg.name)


# MARK: Scripts


def build_script_env(
    manifest: MachineManifest,
    machine_id: str,
    root: Path,
) -> dict[str, str]:
    """Build and resolve the env dict injected into every script subprocess."""
    raw = {
        "MC_HOME": str(root),
        "MC_ID": machine_id,
        "MC_NAME": manifest.name or machine_id,
        **manifest.env,
    }
    env = {k: os.path.expandvars(v) for k, v in raw.items()}
    for _ in range(len(env)):  # converge chained $VAR references
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
    return False


def filter_scripts(scripts: list[str]) -> list[str]:
    """Return scripts that match the current platform and are runnable."""
    return [
        s
        for s in scripts
        if (p := Path(s)).suffix.lower() in _SCRIPT_SUFFIXES and matches_platform(p) and p.exists()
    ]


def run_scripts(
    scripts: list[str],
    env: dict[str, str] | None = None,
    on_before: Callable[[str], None] | None = None,
    on_after: Callable[[str], None] | None = None,
) -> None:
    """Run pre-filtered scripts, respecting ``once_``/``watch_`` tracking.

    Expects scripts already filtered by :func:`filter_scripts`.
    """
    if not scripts:
        return

    state = _load_state()
    logger.info("Scripts: %d to run", len(scripts))

    for script in (Path(s) for s in scripts):
        tracked = script.name.startswith(("once_", "watch_"))

        # Check tracking: once_ run once, watch_ re-run on file change
        if tracked and script.name in state:
            if script.name.startswith("once_"):
                logger.debug("Skip (already ran): %s", script.name)
                if on_after:
                    on_after(script.stem)
                continue
            cur_hash = hashlib.sha256(script.read_bytes()).hexdigest()[:16]
            if state[script.name].get("hash") == cur_hash:
                logger.debug("Skip (unchanged): %s", script.name)
                if on_after:
                    on_after(script.stem)
                continue

        if on_before:
            on_before(script.stem)
        _execute(script, env)

        if tracked:
            state[script.name] = {
                "hash": hashlib.sha256(script.read_bytes()).hexdigest()[:16],
                "ran": datetime.now(timezone.utc).isoformat(),
            }
        if on_after:
            on_after(script.stem)

    _save_state(state)


def _execute(script: Path, env: dict[str, str] | None = None) -> bool:
    """Run a script with inherited stdio. Returns True on success."""
    if is_unix and not os.access(script, os.X_OK):
        os.chmod(script, 0o755)

    logger.info("Run: %s", script.name)

    if settings.dry_run:
        logger.info("[dry-run] %s", script.name)
        return True

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

    merged_env = {**os.environ, **(env or {})}
    exe = shutil.which("powershell.exe") if PLATFORM == Platform.WINDOWS else None

    proc = subprocess.run(cmd, shell=True, executable=exe, env=merged_env)
    if proc.returncode != 0:
        logger.error("Script failed (exit %d): %s", proc.returncode, script.name)
        return False
    return True


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
