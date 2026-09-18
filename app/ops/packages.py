"""Install and upgrade packages using the loader's resolved source choices."""

import subprocess
from collections import defaultdict

from app import managers as package_managers
from app.models import Package, PackageSource, PkgManager
from app.shell import find_executable, run

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Install Packages
# ═════════════════════════════════════════════════════════════════════════════


def install_packages(
    packages: list[Package], *, env: dict[str, str], dry_run: bool, reporter=print
) -> None:
    """Install missing packages, stopping at the first failure."""
    installed: defaultdict[tuple[PackageSource, str], bool] = defaultdict(bool)
    for package in packages:
        try:
            # Run custom setup only when its command is missing.
            if not (source := package.selected_source):
                if not dry_run and find_executable(package.name, env=env):
                    reporter(f"Already installed: cmd -> {package.name}")
                    continue  # Already on PATH (ignored during dry runs for reporting).

                assert package.cmd is not None
                reporter(f"Installing: cmd -> {package.name}")
                run(package.cmd, env=env, dry_run=dry_run, check=True)
                reporter(f"Installed: cmd -> {package.name}")
                continue

            # Require the selected manager.
            manager = PkgManager.BREW if source == "cask" else PkgManager(source)
            available = find_executable(manager, env=env)
            if not available and not dry_run:
                raise FileNotFoundError(f"Selected manager is unavailable: {manager}")

            # Query and cache each package; skip packages already installed.
            package_id = package.sources[source]
            key = (source, str(package_id))
            if not dry_run and available and key not in installed:
                installed[key] = package_managers.source_installed(source, package_id, env=env)
            if available and installed.get(key, False):
                reporter(f"Already installed: {source} -> {package.name}")
                continue  # Ignored during dry runs for reporting.

            # Install the missing package.
            reporter(f"Installing: {source} -> {package.name}")
            package_managers.install_package(package, env=env, dry_run=dry_run)
            reporter(f"Installed: {source} -> {package.name}")

            # Cache only if not in dry-run mode to detect duplocate dependencies.
            if not dry_run:
                installed[key] = True
        except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
            raise RuntimeError(
                f"Failed to install {package.selected_source or 'cmd'} -> {package.name}: {exc}"
            ) from exc


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Upgrade Packages
# ═════════════════════════════════════════════════════════════════════════════


def upgrade_packages(
    packages: list[Package], *, env: dict[str, str], dry_run: bool, reporter=print
) -> list[str]:
    """Upgrade command-backed packages and return names requiring manual maintenance."""
    manual: list[str] = []
    for package in packages:
        # Skip packages managed by a package manager.
        if package.selected_source is not None:
            continue

        # Track packages without an upgrade command for manual maintenance.
        if not package.up_cmd:
            manual.append(package.name)
            continue

        # Use the setup command if requested.
        command = package.cmd if package.up_cmd is True else package.up_cmd
        assert command is not None

        reporter(f"Upgrading: cmd -> {package.name}")
        try:  # Run the upgrade command and stop on the first failure.
            run(command, env=env, dry_run=dry_run, check=True)
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            raise RuntimeError(f"Failed to upgrade cmd -> {package.name}: {exc}") from exc
        reporter(f"Upgraded: cmd -> {package.name}")
    return manual
