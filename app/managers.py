"""Live package-manager readiness, installation, presence, and maintenance."""

import json
from pathlib import Path

from app.env import is_windows
from app.models import Package, PackageSource, PkgManager
from app.ops.scripts import run_scripts
from app.shell import find_executable, query, run

# =============================================================================
# MARK: Validate & Setup
# =============================================================================


def validate_managers(
    managers: list[PkgManager], *, env: dict[str, str], for_upgrade: bool = False
) -> None:
    """Require live prerequisites that the requested workflow cannot install."""
    available = {manager for manager in managers if find_executable(manager, env=env)}
    for manager in managers:
        if manager in available:
            continue
        if for_upgrade or manager in {PkgManager.APT, PkgManager.WINGET}:
            raise FileNotFoundError(f"{manager} must already be installed and available on PATH")
        if manager == PkgManager.SNAP and PkgManager.APT not in available:
            raise FileNotFoundError("Installing snap requires declared apt available on PATH")


def setup_managers(managers: list[PkgManager], *, env: dict[str, str], dry_run: bool) -> None:
    """Install missing declared managers using the host's bundled setup script."""
    if not managers:
        return
    if all(find_executable(manager, env=env) for manager in managers):
        return

    suffix = "win.ps1" if is_windows else "unix.sh"
    script = Path(__file__).parent / "scripts" / f"setup_managers.{suffix}"
    script_env = {**env, "MC_PKG_MANAGERS": " ".join(managers)}
    run_scripts([str(script)], env=script_env, dry_run=dry_run)


# =============================================================================
# MARK: Install
# =============================================================================


def install_package(package: Package, *, env: dict[str, str], dry_run: bool) -> None:
    """Install a resolved manager package and interpret that manager's result."""
    source = package.selected_source
    assert source is not None
    value = str(package.sources[source])
    match source:
        case "brew":
            command = ["brew", "install", value]
        case "cask":
            command = ["brew", "install", "--cask", value]
        case "apt":
            command = ["sudo", "apt", "install", "-y", value]
        case "snap":
            command = ["sudo", "snap", "install", value]
            if package.snap_classic:
                command.append("--classic")
        case "winget":
            command = [
                "winget",
                "install",
                "--id",
                value,
                "--accept-source-agreements",
                "--accept-package-agreements",
            ]
        case "scoop":
            command = ["scoop", "install", value]
        case "mas":
            command = ["mas", "install", value]

    # Treat an already-installed Winget package without upgrades as a successful no-op.
    result = run(
        command,
        env=env,
        dry_run=dry_run,
        capture_output=source == "winget",
        echo_output=source == "winget",
        check=source != "winget",
    )
    if result is None or source != "winget" or result.returncode == 0:
        return
    output = (result.stdout or b"").decode(errors="replace").lower()
    if "found an existing package already installed" in output and any(
        message in output
        for message in (
            "no available upgrade found",
            "no newer package versions are available from the configured sources",
        )
    ):
        return
    raise RuntimeError(f"Winget installation failed (exit {result.returncode}): {value}")


# =============================================================================
# MARK: Upgrade
# =============================================================================


def upgrade_managers(managers: list[PkgManager], *, env: dict[str, str], dry_run: bool) -> None:
    """Upgrade and clean up all packages belonging to the declared managers."""
    for manager in managers:
        match manager:
            case PkgManager.BREW:
                commands = [
                    ["brew", "update"],
                    ["brew", "upgrade"],
                    ["brew", "upgrade", "--cask", "--greedy-latest"],
                    ["brew", "autoremove"],
                    ["brew", "cleanup", "--prune=all"],
                    ["brew", "services", "cleanup"],
                ]
            case PkgManager.MAS:
                commands = [["mas", "upgrade"]]
            case PkgManager.APT:
                commands = [
                    ["sudo", "apt", "update", "-y"],
                    ["sudo", "apt", "upgrade", "-y"],
                    ["sudo", "apt", "autoremove", "-y"],
                ]
            case PkgManager.SNAP:
                commands = [["sudo", "snap", "refresh"]]
            case PkgManager.WINGET:
                commands = [
                    ["winget", "source", "update"],
                    [
                        "winget",
                        "upgrade",
                        "--all",
                        "--accept-package-agreements",
                        "--accept-source-agreements",
                    ],
                ]
            case PkgManager.SCOOP:
                commands = [
                    ["scoop", "update"],
                    ["scoop", "update", "*"],
                    ["scoop", "cleanup", "*"],
                ]

        for command in commands:
            run(command, env=env, dry_run=dry_run, check=True)


# =============================================================================
# MARK: Query
# =============================================================================


def source_installed(source: PackageSource, value: str | int, *, env: dict[str, str]) -> bool:
    """Find the exact installed package identity; failed queries raise."""
    identity = str(value)
    match source:
        case "brew" | "cask":
            flag = "--formula" if source == "brew" else "--cask"
            result = query(["brew", "info", "--json=v2", flag, identity], env=env)
            entries = json.loads(result.stdout)["formulae" if source == "brew" else "casks"]
            return any(entry["installed"] for entry in entries)
        case "mas":
            result = query(["mas", "list"], env=env)
            return any(
                line.split()[0] == identity for line in result.stdout.splitlines() if line.strip()
            )
        case "apt":
            result = query(["dpkg-query", "-W", "-f=${Package}\t${Status}\n"], env=env)
            return any(
                line.split("\t", 1) == [identity, "install ok installed"]
                for line in result.stdout.splitlines()
            )
        case "snap":
            result = query(["snap", "list"], env=env)
            return any(
                fields[0] == identity
                for line in result.stdout.splitlines()[1:]
                if (fields := line.split())
            )
        case "scoop":
            # Export provides exact names without the list command's regex/no-match ambiguity.
            result = query(["scoop", "export"], env=env)
            apps = json.loads(result.stdout)["apps"]
            return any(
                app["Name"].casefold() == identity.rsplit("/", 1)[-1].casefold() for app in apps
            )
        case "winget":
            result = query(["winget", "list", "--id", identity], env=env, check=False)
            # APPINSTALLER_CLI_ERROR_NO_APPLICATIONS_FOUND, including signed Windows exits.
            if result.returncode & 0xFFFFFFFF == 0x8A150014:
                return False
            result.check_returncode()
            return identity.casefold() in {field.casefold() for field in result.stdout.split()}
