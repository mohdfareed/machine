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
    sources: set[PackageSource] = {
        package.selected_source for package in packages if package.selected_source
    }
    installed: dict[PackageSource, set[str]] = (
        {} if dry_run else package_managers.installed_packages(sources, env=env)
    )

    for package in packages:
        # Run custom setup only when its command is missing.
        if not (source := package.selected_source):
            if not dry_run and find_executable(package.name, env=env):
                detail(f"Already installed: cmd -> {package.name}")
                continue  # Already on PATH (ignored during dry runs for reporting).

            assert package.cmd is not None
            run(package.cmd, env=env, dry_run=dry_run, check=True)
            continue

        # Match the selected manager's identity against this deployment's inventory.
        identity = str(package.sources[source])
        if source == "scoop":
            identity = identity.rsplit("/", 1)[-1]
        if source in ("scoop", "winget"):
            identity = identity.casefold()
        if not dry_run and identity in installed[source]:
            detail(f"Already installed: {source} -> {package.name}")
            continue  # Ignored during dry runs for reporting.

        # Install the missing package.
        package_managers.install_package(package, env=env, dry_run=dry_run)

        # Cache only real installations to avoid duplicate dependencies.
        if not dry_run:
            installed[source].add(identity)


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
