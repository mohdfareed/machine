"""Dotfile deployment, package installation, and script execution."""

import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import threading
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from machine.core import PLATFORM, Platform, is_unix, run, settings
from machine.manifest import FileMapping, Module, Package

logger = logging.getLogger(__name__)

_STATE_FILE = settings.app_dir / "state.json"


# MARK: Validation


def validate(
    modules: list[Module],
    manifest_env: dict[str, str],
    machine_id: str,
) -> list[str]:
    """Validate resolved modules against the manifest. Returns a list of errors."""
    errors: list[str] = []

    # Runtime env keys that mc setup always provides
    runtime_keys = {"MC_HOME", "MC_ID", "MC_NAME"}
    provided = runtime_keys | manifest_env.keys()

    for mod in modules:
        for var in mod.required_env:
            if var not in provided:
                errors.append(
                    f"Module '{mod.name}' requires env '{var}' "
                    f"but '{machine_id}' does not provide it"
                )

        for fm in mod.files:
            src = Path(fm.source)
            if not src.exists():
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
        src = Path(fm.source)  # already resolved to absolute by loader
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
    on_advance: Callable[[str], None] | None = None,
) -> None:
    """Install packages using available managers."""
    if not packages:
        return

    managers = {
        name
        for name in ("brew", "apt", "snap", "winget", "scoop", "mas")
        if shutil.which(name)
    }
    logger.info("Managers: %s", ", ".join(sorted(managers)) or "none")

    for pkg in packages:
        _install(pkg, managers)
        if on_advance:
            on_advance(pkg.name)


def upgrade_packages(
    on_advance: Callable[[str], None] | None = None,
) -> None:
    """Upgrade all packages using available managers."""
    _upgrade_cmds: dict[str, str] = {
        "brew": "brew upgrade",
        "apt": "sudo apt upgrade -y",
        "snap": "sudo snap refresh",
        "winget": (
            "winget upgrade --all"
            " --accept-source-agreements --accept-package-agreements"
        ),
        "scoop": "scoop update *",
        "mas": "mas upgrade",
    }
    managers = [
        name
        for name in ("brew", "apt", "snap", "winget", "scoop", "mas")
        if shutil.which(name)
    ]
    logger.info("Upgrading via: %s", ", ".join(managers) or "none")
    for mgr in managers:
        cmd = _upgrade_cmds[mgr]
        logger.info("Upgrade: %s", mgr)
        result = run(cmd, check=False, capture=True)
        if result.stdout:
            for line in result.stdout.strip().splitlines():
                logger.debug("%s: %s", mgr, line)
        if result.returncode != 0:
            logger.error("Upgrade failed: %s (exit %d)", mgr, result.returncode)
        if on_advance:
            on_advance(mgr)


def _install(pkg: Package, managers: set[str]) -> None:
    for mgr, val in _sources(pkg, managers):
        if mgr == "script":
            logger.info("%s: script", pkg.name)
            result = run(val, check=False, capture=True)
        else:
            logger.info("%s: %s", pkg.name, mgr)
            result = run(_cmd(mgr, val), check=False, capture=True)
        if result.stdout:
            for line in result.stdout.strip().splitlines():
                logger.debug("%s: %s", pkg.name, line)
        if result.stderr:
            for line in result.stderr.strip().splitlines():
                logger.debug("%s: %s", pkg.name, line)
        if result.returncode != 0:
            log_file = settings.app_dir / "mc.log"
            logger.error(
                "Failed to install %s (exit %d) — see %s",
                pkg.name,
                result.returncode,
                log_file,
            )
        return
    logger.warning("No manager for: %s", pkg.name)


def _sources(pkg: Package, managers: set[str]) -> list[tuple[str, str]]:
    opts: list[tuple[str, str]] = []
    if pkg.brew and "brew" in managers:
        opts.append(("brew", pkg.brew))
    if pkg.apt and "apt" in managers:
        opts.append(("apt", pkg.apt))
    if pkg.snap and "snap" in managers:
        opts.append(("snap", pkg.snap))
    if pkg.winget and "winget" in managers:
        opts.append(("winget", pkg.winget))
    if pkg.scoop and "scoop" in managers:
        opts.append(("scoop", pkg.scoop))
    if pkg.mas is not None and "mas" in managers:
        opts.append(("mas", str(pkg.mas)))
    if pkg.script:
        opts.append(("script", pkg.script))
    return opts


def _cmd(manager: str, value: str) -> str:
    match manager:
        case "brew":
            return f"brew install {value}"
        case "apt":
            return f"sudo apt install -y {value}"
        case "snap":
            return f"sudo snap install {value}"
        case "winget":
            return (
                "winget install --accept-source-agreements "
                f"--accept-package-agreements {value}"
            )
        case "scoop":
            return f"scoop install {value}"
        case "mas":
            return f"mas install {value}"
        case _:
            raise ValueError(f"Unknown manager: {manager}")


# MARK: Scripts


def run_scripts(
    scripts: list[str],
    env: dict[str, str] | None = None,
    on_advance: Callable[[str], None] | None = None,
) -> None:
    """Run scripts (absolute paths), respecting platform tags and tracking.

    ``env`` is injected into every script subprocess on top of the
    current process environment (e.g. MC_HOME, MC_ID, manifest vars).
    """
    resolved = [Path(s) for s in scripts if _matches_platform(Path(s))]
    resolved = [s for s in resolved if s.exists() and _runnable(s)]

    if not resolved:
        return

    state = _load_state()
    logger.info("Scripts: %d to run", len(resolved))

    for script in resolved:
        if _is_tracked(script) and not _should_run(script, state):
            logger.debug("Skip: %s", script.name)
        else:
            _execute(script, env)
            if _is_tracked(script):
                _mark_run(script, state)
        if on_advance:
            on_advance(script.stem)

    _save_state(state)


def _runnable(path: Path) -> bool:
    return path.suffix.lower() in {".sh", ".py", ".ps1"}


def filter_scripts(scripts: list[str]) -> list[str]:
    """Return scripts that match the current platform and are runnable."""
    return [
        s
        for s in scripts
        if _matches_platform(Path(s)) and Path(s).exists() and _runnable(Path(s))
    ]


def _matches_platform(script: Path) -> bool:
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


def _execute(script: Path, env: dict[str, str] | None = None) -> bool:
    """Run a script, streaming output to terminal and file log."""
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

    if settings.debug:
        # Pass through directly — no capture, no logger formatting.
        proc = subprocess.run(cmd, shell=True, executable=exe, env=merged_env)
        if proc.returncode != 0:
            logger.error("Script failed (exit %d): %s", proc.returncode, script.name)
            return False
        return True

    proc = subprocess.Popen(
        cmd,
        shell=True,
        executable=exe,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=merged_env,
    )

    def _stream(pipe, level):  # type: ignore[no-untyped-def]
        for line in pipe:
            logger.log(level, "%s: %s", script.name, line.rstrip())

    t_out = threading.Thread(target=_stream, args=(proc.stdout, logging.DEBUG))
    t_err = threading.Thread(target=_stream, args=(proc.stderr, logging.WARNING))
    t_out.start()
    t_err.start()
    t_out.join()
    t_err.join()
    proc.wait()

    if proc.returncode != 0:
        log_file = settings.app_dir / "mc.log"
        logger.error(
            "Script failed (exit %d): %s — see %s",
            proc.returncode,
            script.name,
            log_file,
        )
        return False
    return True


def _is_tracked(script: Path) -> bool:
    return script.name.startswith(("once_", "watch_"))


def _should_run(script: Path, state: dict) -> bool:
    key = script.name
    if key not in state:
        return True
    if script.name.startswith("watch_"):
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
