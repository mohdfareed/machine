"""Package installation and manager detection."""

import logging
import os
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from machine.core import PLATFORM, Platform, is_windows, run_collect, settings
from machine.manifest import Package, PkgManager

logger = logging.getLogger(__name__)

type PackageSource = Literal["brew", "cask", "apt", "snap", "winget", "scoop", "mas"]


@dataclass(frozen=True, slots=True)
class ManagerConfig:
    binary: str
    install_cmd: str


_PLATFORM_SOURCES: dict[Platform, tuple[PackageSource, ...]] = {
    Platform.MACOS: ("cask", "brew", "mas"),
    Platform.LINUX: ("apt", "snap", "brew"),
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

    if is_windows or settings.dry_run or _sudo_keepalive is not None:
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
    # Equivalent to `is_windows` but is a statically known platform guard.
    if sys.platform == "win32":
        import winreg

        paths = [os.environ.get("PATH", "")]
        for hive, key in (
            (
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
            ),
            (winreg.HKEY_CURRENT_USER, "Environment"),
        ):
            try:
                with winreg.OpenKey(hive, key) as handle:
                    value, _ = winreg.QueryValueEx(handle, "Path")
                    paths.append(os.path.expandvars(value))
            except OSError:
                pass

        # Deduplicate directories, not whole PATH strings, so repeated refreshes cannot grow PATH.
        entries = (entry for path in paths for entry in path.split(os.pathsep) if entry)
        unique: dict[str, str] = {}
        for entry in entries:
            unique.setdefault(os.path.normcase(os.path.normpath(entry)), entry)

        os.environ["PATH"] = os.pathsep.join(unique.values())
        return

    try:
        shell = os.environ.get("SHELL", "/bin/sh")
        out = subprocess.check_output([shell, "-lc", "echo $PATH"], text=True, timeout=5).strip()

        if out:
            os.environ["PATH"] = out
            logger.debug("Refreshed PATH: %s", out)
    except Exception as exc:
        logger.debug("PATH refresh failed: %s", exc)

    for directory in ("/opt/homebrew/bin", "/usr/local/bin", "/home/linuxbrew/.linuxbrew/bin"):
        if (Path(directory) / "brew").is_file():
            os.environ["PATH"] = directory + os.pathsep + os.environ.get("PATH", "")
            break


def validate_managers(managers: list[PkgManager]) -> None:
    """Validate explicit manager declarations before running setup scripts."""
    supported = {
        _MANAGER_CONFIGS[source].binary
        for platform, sources in _PLATFORM_SOURCES.items()
        if PLATFORM.is_a(platform)
        for source in sources
    }

    for manager in managers:
        if manager not in supported:
            raise ValueError(f"{manager} is not supported on {PLATFORM}")

    if PkgManager.MAS in managers and PkgManager.BREW not in managers:
        raise ValueError("mas requires brew in pkg_managers")
    if PkgManager.APT in managers and not shutil.which("apt"):
        raise ValueError("apt must already be installed")
    if PkgManager.SNAP in managers and not shutil.which("snap") and PkgManager.APT not in managers:
        raise ValueError("Installing snap requires apt in pkg_managers")


def install_packages(
    packages: list[Package],
    managers: list[PkgManager],
    owners: dict[str, str] | None = None,
    rerun_script_packages: bool = False,
) -> list[tuple[str, str, str]]:
    """Resolve, check, and install packages using only declared managers."""
    if not packages:
        return []

    refresh_path()
    available = {manager for manager in managers if shutil.which(manager)}
    installed: dict[tuple[PackageSource, str], bool] = {}
    failures: list[tuple[str, str, str]] = []

    for pkg in packages:
        if not pkg.applies_to(PLATFORM):
            continue
        module = (owners or {}).get(pkg.name, "?")

        try:
            source = select_package_source(pkg, managers, None if settings.dry_run else available)
            if source is not None:
                # A dry run can plan installs before manager setup has run.
                key = (source, str(getattr(pkg, source)))

                if _MANAGER_CONFIGS[source].binary in available:
                    if key not in installed:
                        installed[key] = _source_installed(source, getattr(pkg, source))
                    if installed[key]:
                        logger.debug("Skip (installed): %s", pkg.name)
                        continue

            elif not pkg.script:
                continue
            elif not rerun_script_packages and shutil.which(pkg.name):
                logger.debug("Skip (installed): %s", pkg.name)
                continue

            failure = _install(pkg, source, module)
            if failure:
                failures.append(failure)
            elif source is not None and not settings.dry_run:
                installed[(source, str(getattr(pkg, source)))] = True

        except (ValueError, OSError, subprocess.SubprocessError) as exc:
            logger.error("[%s] %s: %s", module, pkg.name, exc)
            failures.append((module, pkg.name, str(exc)))
    return failures


def select_package_source(
    pkg: Package,
    managers: list[PkgManager],
    available: set[PkgManager] | None = None,
) -> PackageSource | None:
    """Select a declared source; omit availability when previewing manager setup."""
    sources = _applicable_sources(pkg)
    if not sources:
        return None

    declared: list[PackageSource] = [
        source for source in sources if _MANAGER_CONFIGS[source].binary in managers
    ]

    if not declared:
        raise ValueError(
            "manager not declared: "
            + ", ".join(dict.fromkeys(_MANAGER_CONFIGS[source].binary for source in sources))
        )

    for source in declared:
        if available is None or _MANAGER_CONFIGS[source].binary in available:
            return source
    raise ValueError("no manager available")


def _install(
    pkg: Package, source: PackageSource | None, module: str = "?"
) -> tuple[str, str, str] | None:
    """Execute an already-resolved manager or script installation."""
    cmd = (
        _MANAGER_CONFIGS[source].install_cmd.format(getattr(pkg, source))
        if source is not None
        else pkg.script
    )
    assert cmd is not None

    logger.info("[%s] %s: %s", module, pkg.name, source or "script")
    rc, output = run_collect(cmd, label=module)
    if _install_succeeded(source, rc, output):
        return None

    logger.error("[%s] failed to install %s (exit %d): %s", module, pkg.name, rc, cmd)
    return (module, pkg.name, f"{source or 'script'} exit {rc}")


def _install_succeeded(manager: PackageSource | None, rc: int, output: bytes | bytearray) -> bool:
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


def _applicable_sources(pkg: Package) -> list[PackageSource]:
    """Return platform-compatible sources in preference order."""
    if not pkg.applies_to(PLATFORM):
        return []

    return [
        source
        for platform, sources in _PLATFORM_SOURCES.items()
        if PLATFORM.is_a(platform)
        for source in sources
        if getattr(pkg, source) is not None
    ]


def _source_installed(source: PackageSource, value: str | int) -> bool:
    """Query the selected manager for this package's installed status."""
    match source:
        case "brew" | "cask":
            cmd = ["brew", "list", "--formula" if source == "brew" else "--cask", str(value)]

        case "mas":
            lines = _query(["mas", "list"], check=True).stdout.splitlines()
            return any(line.split()[0] == str(value) for line in lines if line.strip())

        case "apt":
            result = _query(["dpkg-query", "-W", "-f=${Status}", str(value)])
            return result.returncode == 0 and "install ok installed" in result.stdout.lower()

        case "snap" | "scoop":
            cmd = [source, "list", str(value)]

        case "winget":
            # --exact is case-sensitive; compare the full ID ourselves after the ID-filtered query.
            result = _query(["winget", "list", "--id", str(value)])
            return result.returncode == 0 and str(value).casefold() in {
                field.casefold() for field in result.stdout.split()
            }

        case _:
            raise AssertionError(f"Unhandled package source: {source}")
    return _query(cmd).returncode == 0


def _query(cmd: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    """Run a presence query, resolving Windows shims and bounding execution time."""
    executable = shutil.which(cmd[0])
    if executable is None:
        raise FileNotFoundError(f"Manager query executable not found: {cmd[0]}")
    return subprocess.run(
        [executable, *cmd[1:]], capture_output=True, text=True, timeout=30, check=check
    )
