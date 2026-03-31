"""Dotfile deployment, package installation, and script execution."""

import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from machine.core import PLATFORM, Platform, err_console, is_unix, run, run_collect, settings
from machine.manifest import SCRIPT_SUFFIXES, FileMapping, Module, Package

logger = logging.getLogger(__name__)

# Structured failure record for end-of-run summaries
type Failure = tuple[str, str, str]  # (module, item, detail)
type PackageSource = Literal["brew", "cask", "apt", "snap", "winget", "scoop", "mas"]


@dataclass(frozen=True, slots=True)
class ManagerConfig:
    binary: str
    install_cmd: str


_STATE_FILE = settings.app_dir / "state.json"
_MACHINE_FILE = settings.app_dir / "machine.txt"
_PLATFORM_SOURCES: dict[Platform, tuple[PackageSource, ...]] = {
    Platform.MACOS: ("cask", "brew", "mas"),
    Platform.LINUX: ("apt", "snap", "brew"),
    Platform.WSL: ("apt", "snap", "brew"),
    Platform.GHCS: ("apt", "snap", "brew"),
    Platform.WINDOWS: ("winget", "scoop"),
}
_MANAGER_CONFIGS: dict[PackageSource, ManagerConfig] = {
    "brew": ManagerConfig(binary="brew", install_cmd="brew install {}"),
    "cask": ManagerConfig(binary="brew", install_cmd="brew install --cask {}"),
    "apt": ManagerConfig(binary="apt", install_cmd="sudo apt install -y {}"),
    "snap": ManagerConfig(binary="snap", install_cmd="sudo snap install {}"),
    "winget": ManagerConfig(
        binary="winget",
        install_cmd="winget install --accept-source-agreements --accept-package-agreements {}",
    ),
    "scoop": ManagerConfig(binary="scoop", install_cmd="scoop install {}"),
    "mas": ManagerConfig(binary="mas", install_cmd="mas install {}"),
}

# # MARK: Sudo

_sudo_keepalive: threading.Event | None = None


def cache_sudo() -> None:
    """Prompt for sudo once and keep credentials alive in the background."""
    global _sudo_keepalive

    if not is_unix or settings.dry_run or _sudo_keepalive is not None:
        return

    # Initial prompt - the only interactive one.
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


# # MARK: Validation


def validate(
    modules: list[Module],
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


# # MARK: Files


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
        else:
            try:
                if _symlink(src, tgt):
                    created += 1
            except OSError as exc:
                logger.error("[%s] failed to link %s → %s: %s", module, tgt, src, exc)
                failures.append((module, str(tgt), str(exc)))
    return created, failures


def _symlink(source: Path, target: Path) -> bool:
    """Create or update a symlink. Returns True if changed."""

    def _norm(path: Path) -> str:
        try:
            return os.path.normcase(str(path.resolve(strict=False)))
        except OSError:
            return os.path.normcase(str(path.absolute()))

    def _points_to_source(link_path: Path, src_path: Path) -> bool:
        try:
            link_target = link_path.readlink()
        except OSError:
            return False

        if not link_target.is_absolute():
            link_target = link_path.parent / link_target

        return _norm(link_target) == _norm(src_path)

    if settings.dry_run:
        if target.is_symlink() and _points_to_source(target, source):
            return False
        logger.info("[dry-run] link %s → %s", target, source)
        return True

    target.parent.mkdir(parents=True, exist_ok=True)

    if target.is_symlink():
        if _points_to_source(target, source):
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


# # MARK: Packages


def refresh_path() -> None:
    """Re-read PATH from a login shell so managers installed by init scripts
    (e.g. Homebrew on a fresh Mac) are visible to ``shutil.which``."""
    if not is_unix:
        return
    try:
        shell = os.environ.get("SHELL", "/bin/sh")
        out = subprocess.check_output([shell, "-lc", "echo $PATH"], text=True, timeout=5).strip()
        if out:
            os.environ["PATH"] = out
            logger.debug("Refreshed PATH: %s", out)
    except Exception as exc:
        logger.debug("PATH refresh failed: %s", exc)


def install_packages(
    packages: list[Package],
    owners: dict[str, str] | None = None,
) -> list[Failure]:
    """Install packages using available managers. Returns list of failures."""
    if not packages:
        return []

    # Re-read PATH from a login shell so managers installed by prior init
    # scripts (e.g. Homebrew) are discoverable via shutil.which.
    refresh_path()

    manager_bins = _available_manager_bins()
    available_sources = _available_sources(manager_bins)
    logger.info("Managers: %s", ", ".join(sorted(manager_bins)) or "none")

    failures: list[Failure] = []
    skipped_installed = 0
    skipped_inapplicable = 0
    for pkg in packages:
        current_bins = _available_manager_bins()
        if current_bins != manager_bins:
            manager_bins = current_bins
            available_sources = _available_sources(manager_bins)
            logger.info("Managers: %s", ", ".join(sorted(manager_bins)) or "none")

        applicable_sources = _applicable_sources(pkg)
        can_run_script = bool(pkg.script and pkg.applies_to(PLATFORM))
        if not applicable_sources and not can_run_script:
            logger.debug("Skip (not applicable): %s", pkg.name)
            skipped_inapplicable += 1
            continue

        installed_with_manager = _installed_with_requested_manager(
            pkg,
            available_sources,
            applicable_sources,
        )
        if installed_with_manager:
            logger.debug("Skip (installed): %s", pkg.name)
            skipped_installed += 1
            continue
        module = (owners or {}).get(pkg.name, "?")
        fail = _install(pkg, available_sources, applicable_sources, can_run_script, module)
        if fail:
            failures.append(fail)

    if skipped_installed:
        logger.info("Skipped %d already-installed package(s)", skipped_installed)
    if skipped_inapplicable:
        logger.info("Skipped %d package(s) that do not apply on %s", skipped_inapplicable, PLATFORM)
    return failures


def _install(
    pkg: Package,
    available_sources: set[PackageSource],
    applicable_sources: list[PackageSource],
    can_run_script: bool,
    module: str = "?",
) -> Failure | None:
    """Try to install a package. Returns a Failure on error, else None."""
    source = _selected_source(applicable_sources, available_sources)
    if source is not None:
        val = _package_source_value(pkg, source)
        if val is None:
            raise AssertionError(f"Missing package source '{source}' for {pkg.name}")

        cmd = _MANAGER_CONFIGS[source].install_cmd.format(val)
        logger.info("[%s] %s: %s", module, pkg.name, source)
        rc, output = run_collect(cmd, label=module)
        if _install_succeeded(source, rc, output):
            if source == "winget" and rc != 0:
                logger.info("[%s] %s already installed; no upgrade available", module, pkg.name)
            return None
        if rc != 0:
            logger.error(
                "[%s] failed to install %s via %s (exit %d): %s",
                module,
                pkg.name,
                source,
                rc,
                cmd,
            )
            return (module, pkg.name, f"{source} exit {rc}")
        return None

    if applicable_sources:
        logger.warning("[%s] no manager for: %s", module, pkg.name)
        return (module, pkg.name, "no manager available")

    if can_run_script and pkg.script:
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

    logger.debug("[%s] skip %s: no applicable package source on %s", module, pkg.name, PLATFORM)
    return None


def _install_succeeded(
    manager: PackageSource,
    rc: int,
    output: bytes | bytearray,
) -> bool:
    """Classify manager exit codes that should count as a successful no-op."""
    if rc == 0:
        return True
    if manager != "winget":
        return False
    text = output.decode(errors="replace").lower()
    return "found an existing package already installed" in text and any(
        msg in text
        for msg in (
            "no available upgrade found",
            "no newer package versions are available from the configured sources",
        )
    )


def _installed_with_requested_manager(
    pkg: Package,
    available_sources: set[PackageSource],
    applicable_sources: list[PackageSource],
) -> bool:
    """Return True when the package is already present under its requested manager."""
    source = _selected_source(applicable_sources, available_sources)
    if source is None:
        return False
    value = _package_source_value(pkg, source)
    if value is None:
        return False
    return _source_installed(source, value)


def _applicable_sources(pkg: Package) -> list[PackageSource]:
    """Return package sources that make sense on the current platform."""
    if not pkg.applies_to(PLATFORM):
        return []
    return [
        source
        for source in _PLATFORM_SOURCES[PLATFORM]
        if _package_source_value(pkg, source) is not None
    ]


def _available_manager_bins() -> set[str]:
    """Return installed package-manager executables."""
    return {config.binary for config in _MANAGER_CONFIGS.values() if shutil.which(config.binary)}


def _available_sources(manager_bins: set[str]) -> set[PackageSource]:
    """Return package sources whose backing managers are installed."""
    return {source for source, config in _MANAGER_CONFIGS.items() if config.binary in manager_bins}


def _selected_source(
    applicable_sources: list[PackageSource],
    available_sources: set[PackageSource],
) -> PackageSource | None:
    """Return the first applicable source whose manager is installed."""
    for source in applicable_sources:
        if source in available_sources:
            return source
    return None


def _package_source_value(pkg: Package, source: PackageSource) -> str | int | None:
    """Return the package value for a specific install source."""
    return getattr(pkg, source)


def _source_installed(source: PackageSource, value: str | int) -> bool:
    """Return True when the requested manager already has the package installed."""
    match source:
        case "brew":
            return _command_succeeds(["brew", "list", "--formula", str(value)])
        case "cask":
            return _command_succeeds(["brew", "list", "--cask", str(value)])
        case "apt":
            proc = subprocess.run(
                ["dpkg-query", "-W", "-f=${Status}", str(value)],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            return proc.returncode == 0 and "install ok installed" in proc.stdout.lower()
        case "snap":
            return _command_succeeds(["snap", "list", str(value)])
        case "winget":
            return _winget_installed(str(value))
        case "scoop":
            return _command_succeeds(["scoop", "list", str(value)])
        case "mas":
            return _mas_installed(int(value))

    raise AssertionError(f"Unhandled package source: {source}")


def _command_succeeds(cmd: list[str]) -> bool:
    """Return True when *cmd* exits successfully."""
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return proc.returncode == 0


def _winget_installed(package_id: str) -> bool:
    """Return True when winget already manages the exact package id."""
    proc = subprocess.run(
        ["winget", "list", "--exact", "--id", package_id],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return proc.returncode == 0


def _mas_installed(app_id: int) -> bool:
    """Return True when the Mac App Store app id is already installed."""
    proc = subprocess.run(
        ["mas", "list"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return proc.returncode == 0 and any(
        line.startswith(f"{app_id} ") for line in proc.stdout.splitlines()
    )


# # MARK: Scripts


_ENV_FILE = Path.home() / ".env"


def build_script_env(
    machine_id: str,
    root: Path,
) -> dict[str, str]:
    """Build the env dict injected into every script subprocess.

    Three-tier sourcing:
      1. MC_HOME, MC_ID, MC_PRIVATE (defaults to ``app_dir/private``)
      2. ``machines/<id>/machine.env`` - committed config vars (may override MC_PRIVATE)
      3. ``$MC_PRIVATE/env/$MC_ID.env`` - machine secrets (skipped when dir missing)

    Values may reference earlier vars with ``$VAR``; all references are
    resolved iteratively.
    """
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
                value = value.strip().strip('"').strip("'")
                raw[key.strip()] = value

    # Tier 2: committed machine config vars (may override MC_PRIVATE)
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
    sourced by other scripts - they are never executed directly.
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
                "ran": datetime.now(UTC).isoformat(),
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


# # MARK: Machine


def get_current_machine() -> str | None:
    """Return the last-used machine ID, or None if not set."""
    return _MACHINE_FILE.read_text().strip() if _MACHINE_FILE.exists() else None


def save_current_machine(machine_id: str) -> None:
    """Persist the current machine ID."""
    _MACHINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _MACHINE_FILE.write_text(machine_id)


# # MARK: State


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
