"""Install and upgrade packages using the loader's resolved source choices."""

from app.config.models import Package, PackageSource
from app.deployment import managers as package_managers
from app.runtime.reporting import detail
from app.runtime.shell import find_executable, run

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Install Packages
# ═════════════════════════════════════════════════════════════════════════════


def install_packages(packages: list[Package], *, env: dict[str, str], dry_run: bool) -> None:
    """Install missing packages, stopping at the first failure."""
    installed: dict[tuple[PackageSource, str], bool] = {}
    for package in packages:
        # Run custom setup only when its command is missing.
        if not (source := package.selected_source):
            if not dry_run and find_executable(package.name, env=env):
                detail(f"Already installed: cmd -> {package.name}")
                continue  # Already on PATH (ignored during dry runs for reporting).

            assert package.cmd is not None
            run(package.cmd, env=env, dry_run=dry_run, check=True)
            continue

        # Query and cache each package; skip packages already installed.
        package_id = package.sources[source]
        key = (source, str(package_id))
        if not dry_run and key not in installed:
            installed[key] = package_managers.source_installed(source, package_id, env=env)
        if installed.get(key, False):
            detail(f"Already installed: {source} -> {package.name}")
            continue  # Ignored during dry runs for reporting.

        # Install the missing package.
        package_managers.install_package(package, env=env, dry_run=dry_run)

        # Cache only real installations to avoid duplicate dependencies.
        if not dry_run:
            installed[key] = True


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Upgrade Packages
# ═════════════════════════════════════════════════════════════════════════════


def upgrade_packages(packages: list[Package], *, env: dict[str, str], dry_run: bool) -> list[str]:
    """Run declared upgrade commands and return unmanaged packages needing manual maintenance."""
    manual: list[str] = []
    for package in packages:
        # Only unmanaged packages without an upgrade command need manual maintenance.
        if not package.up_cmd:
            if package.selected_source is None:
                manual.append(package.name)
            continue

        # Use the setup command if requested.
        command = package.cmd if package.up_cmd is True else package.up_cmd
        assert command is not None

        run(command, env=env, dry_run=dry_run, check=True)
    return manual
