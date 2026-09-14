"""Install and upgrade packages using the loader's resolved source choices."""

import subprocess

from app import managers as package_managers
from app.models import Package, PackageSource, PkgManager
from app.shell import find_executable, run

# =============================================================================
# MARK: Install Packages
# =============================================================================


def install_packages(packages: list[Package], *, env: dict[str, str], dry_run: bool) -> list[str]:
    """Install missing packages and return skipped names, stopping at the first failure."""
    installed: dict[tuple[PackageSource, str], bool] = {}
    skipped: list[str] = []
    for package in packages:
        try:
            # Run custom setup only when its command is missing.
            source = package.selected_source
            if source is None:
                if find_executable(package.name, env=env):
                    skipped.append(package.name)
                    continue
                assert package.cmd is not None
                run(package.cmd, env=env, dry_run=dry_run, check=True)
                continue

            # Require the selected manager, allowing previews before its installation.
            manager = PkgManager.BREW if source == "cask" else PkgManager(source)
            available = find_executable(manager, env=env)
            if not available and not dry_run:
                raise FileNotFoundError(f"Selected manager is unavailable: {manager}")

            # Query each package once and skip packages already installed.
            package_id = package.sources[source]
            key = (source, str(package_id))
            if available and key not in installed:
                installed[key] = package_managers.source_installed(source, package_id, env=env)
            if available and installed[key]:
                skipped.append(package.name)
                continue

            # Install the missing package and remember successful changes for this run.
            package_managers.install_package(package, env=env, dry_run=dry_run)
            if not dry_run:
                installed[key] = True
        except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
            raise RuntimeError(f"Failed to install {package.name}: {exc}") from exc
    return skipped


# =============================================================================
# MARK: Upgrade Packages
# =============================================================================


def upgrade_packages(packages: list[Package], *, env: dict[str, str], dry_run: bool) -> list[str]:
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

        try:  # Run the upgrade command and stop on the first failure.
            run(command, env=env, dry_run=dry_run, check=True)
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            raise RuntimeError(f"Failed to upgrade {package.name}: {exc}") from exc
    return manual
