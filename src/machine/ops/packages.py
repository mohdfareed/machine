"""Package installation and manager detection."""

import logging
import os
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass
from typing import Literal

from machine.core import PLATFORM, Platform, is_unix, run, run_collect, settings
from machine.manifest import Package

logger = logging.getLogger(__name__)

type PackageSource = Literal["brew", "cask", "apt", "snap", "winget", "scoop", "mas"]


@dataclass(frozen=True, slots=True)
class ManagerConfig:
    binary: str
    install_cmd: str


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

_sudo_keepalive: threading.Event | None = None


def cache_sudo() -> None:
    """Prompt for sudo once and keep credentials alive in the background."""
    global _sudo_keepalive

    if not is_unix or settings.dry_run or _sudo_keepalive is not None:
        return

    rc = subprocess.call(["sudo", "-v"], stdin=sys.stdin)
    if rc != 0:
        logger.warning("sudo -v failed (exit %d); scripts may re-prompt", rc)
        return

    stop = threading.Event()
    _sudo_keepalive = stop

    def _keepalive() -> None:
        while not stop.wait(60):
            subprocess.call(["sudo", "-v"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    threading.Thread(target=_keepalive, daemon=True).start()


def refresh_path() -> None:
    """Re-read PATH from a login shell so installed managers are visible."""
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
    rerun_script_packages: bool = False,
) -> list[tuple[str, str, str]]:
    """Install packages using available managers. Returns list of failures."""
    if not packages:
        return []

    refresh_path()

    manager_bins = _available_manager_bins()
    available_sources = _available_sources(manager_bins)
    installed_sources = _installed_source_snapshots(available_sources)
    logger.info("Managers: %s", ", ".join(sorted(manager_bins)) or "none")

    failures: list[tuple[str, str, str]] = []
    skipped_installed = 0
    skipped_inapplicable = 0
    for pkg in packages:
        applicable_sources = _applicable_sources(pkg)
        can_run_script = bool(pkg.script and pkg.applies_to(PLATFORM))
        selected_source = _selected_source(applicable_sources, available_sources)
        if not applicable_sources and not can_run_script:
            logger.debug("Skip (not applicable): %s", pkg.name)
            skipped_inapplicable += 1
            continue

        if _installed_with_requested_manager(
            pkg,
            selected_source,
            installed_sources,
            rerun_script_packages=rerun_script_packages,
        ):
            logger.debug("Skip (installed): %s", pkg.name)
            skipped_installed += 1
            continue

        module = (owners or {}).get(pkg.name, "?")
        fail = _install(pkg, selected_source, applicable_sources, can_run_script, module)
        if fail:
            failures.append(fail)

    if skipped_installed:
        logger.info("Skipped %d already-installed package(s)", skipped_installed)
    if skipped_inapplicable:
        logger.info("Skipped %d package(s) that do not apply on %s", skipped_inapplicable, PLATFORM)
    return failures


def _install(
    pkg: Package,
    selected_source: PackageSource | None,
    applicable_sources: list[PackageSource],
    can_run_script: bool,
    module: str = "?",
) -> tuple[str, str, str] | None:
    """Try to install a package. Returns a Failure on error, else None."""
    if selected_source is not None:
        value = _package_source_value(pkg, selected_source)
        if value is None:
            raise AssertionError(f"Missing package source '{selected_source}' for {pkg.name}")

        cmd = _MANAGER_CONFIGS[selected_source].install_cmd.format(value)
        logger.info("[%s] %s: %s", module, pkg.name, selected_source)
        rc, output = run_collect(cmd, label=module)
        if _install_succeeded(selected_source, rc, output):
            if selected_source == "winget" and rc != 0:
                logger.info("[%s] %s already installed; no upgrade available", module, pkg.name)
            return None
        if rc != 0:
            logger.error(
                "[%s] failed to install %s via %s (exit %d): %s",
                module,
                pkg.name,
                selected_source,
                rc,
                cmd,
            )
            return (module, pkg.name, f"{selected_source} exit {rc}")
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


def _install_succeeded(manager: PackageSource, rc: int, output: bytes | bytearray) -> bool:
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
    selected_source: PackageSource | None,
    installed_sources: dict[PackageSource, set[str]],
    rerun_script_packages: bool = False,
) -> bool:
    """Return True when the package is already present under its requested manager."""
    if selected_source is not None:
        value = _package_source_value(pkg, selected_source)
        if value is None:
            return False
        if selected_source in installed_sources:
            return str(value) in installed_sources[selected_source]
        return _source_installed(selected_source, value)

    if rerun_script_packages or not pkg.script or not pkg.name:
        return False

    return shutil.which(pkg.name) is not None


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


def _installed_source_snapshots(
    available_sources: set[PackageSource],
) -> dict[PackageSource, set[str]]:
    """Return bulk-installed package snapshots for managers with cheap list commands."""
    snapshots: dict[PackageSource, set[str]] = {}
    if "brew" in available_sources:
        snapshots["brew"] = _command_output_lines(["brew", "list", "--formula"])
    if "cask" in available_sources:
        snapshots["cask"] = _command_output_lines(["brew", "list", "--cask"])
    if "mas" in available_sources:
        snapshots["mas"] = _mas_installed_ids()
    return snapshots


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


def _command_output_lines(cmd: list[str]) -> set[str]:
    """Return non-empty output lines from *cmd*, or an empty set on failure."""
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        return set()
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


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
    return str(app_id) in _mas_installed_ids()


def _mas_installed_ids() -> set[str]:
    """Return installed Mac App Store app ids from `mas list`."""
    proc = subprocess.run(
        ["mas", "list"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        return set()
    return {parts[0] for line in proc.stdout.splitlines() if (parts := line.split())}
