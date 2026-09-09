"""Package source selection and installation workflow."""

import logging
import shutil
import subprocess

from app.env import PLATFORM, settings
from app.models import Failure, Package, PkgManager
from app.ops import managers as package_managers
from app.ops.managers import PackageSource
from app.shell import refresh_path, run

_logger = logging.getLogger(__name__)

# =============================================================================
# MARK: Install Packages
# =============================================================================


def install_packages(
    packages: list[Package],
    managers: list[PkgManager],
    owners: dict[str, str] | None = None,
    rerun_script_packages: bool = False,
) -> list[Failure]:
    """Resolve, check, and install packages using only declared managers."""
    if not packages:
        return []

    # Discover declared managers and cache package presence for this run.
    refresh_path()
    available = {manager for manager in managers if shutil.which(manager)}
    installed: dict[tuple[PackageSource, str], bool] = {}
    failures: list[Failure] = []

    for pkg in packages:
        if not pkg.applies_to(PLATFORM):
            continue

        module = (owners or {}).get(pkg.name, "?")

        try:
            # Resolve the source and skip packages already installed by that manager.
            source = select_package_source(pkg, managers, None if settings.dry_run else available)
            if source is not None:
                # A dry run can plan installs before manager setup has run.
                key = (source, str(getattr(pkg, source)))

                if package_managers.MANAGER_CONFIGS[source].binary in available:
                    if key not in installed:
                        installed[key] = package_managers.source_installed(
                            source, getattr(pkg, source)
                        )
                    if installed[key]:
                        _logger.debug("Skip (installed): %s", pkg.name)
                        continue

            elif not pkg.script:
                continue
            elif not rerun_script_packages and shutil.which(pkg.name):
                _logger.debug("Skip (installed): %s", pkg.name)
                continue

            # Install missing packages and cache successful manager-backed installs.
            failure = _install(pkg, source, module)
            if failure:
                failures.append(failure)
                continue

            if source is not None and not settings.dry_run:
                installed[(source, str(getattr(pkg, source)))] = True

        except (ValueError, OSError, subprocess.SubprocessError) as exc:
            _logger.error("[%s] %s: %s", module, pkg.name, exc)
            failures.append(Failure(module=module, item=pkg.name, detail=str(exc)))

    return failures


def _install(pkg: Package, source: PackageSource | None, module: str = "?") -> Failure | None:
    cmd = (
        package_managers.MANAGER_CONFIGS[source].install_cmd.format(getattr(pkg, source))
        if source is not None
        else pkg.script
    )
    assert cmd is not None

    _logger.info("[%s] %s: %s", module, pkg.name, source or "script")
    result = run(cmd, label=module, capture_output=True)
    if package_managers.install_succeeded(source, result.returncode, result.stdout):
        return None

    _logger.error(
        "[%s] Failed to install %s (exit %d): %s", module, pkg.name, result.returncode, cmd
    )
    return Failure(
        module=module, item=pkg.name, detail=f"{source or 'script'} exit {result.returncode}"
    )


# =============================================================================
# MARK: Select Package Sources
# =============================================================================


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
        source for source in sources if package_managers.MANAGER_CONFIGS[source].binary in managers
    ]

    if not declared:
        raise ValueError(
            "Manager not declared: "
            + ", ".join(
                dict.fromkeys(package_managers.MANAGER_CONFIGS[source].binary for source in sources)
            )
        )

    for source in declared:
        if available is None or package_managers.MANAGER_CONFIGS[source].binary in available:
            return source

    raise ValueError("No manager available")


def _applicable_sources(pkg: Package) -> list[PackageSource]:
    if not pkg.applies_to(PLATFORM):
        return []

    return [
        source
        for platform, sources in package_managers.PLATFORM_SOURCES.items()
        if PLATFORM.is_a(platform)
        for source in sources
        if getattr(pkg, source) is not None
    ]
