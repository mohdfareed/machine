"""Package-manager setup, installation, presence, and maintenance."""

import json
import tempfile
from pathlib import Path

from app.config.models import Package, PackageSource, PkgManager, Platform
from app.runtime import env as machine_env
from app.runtime.shell import find_executable, query, run

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Setup
# ═════════════════════════════════════════════════════════════════════════════


def setup_managers(managers: list[PkgManager], *, env: dict[str, str], dry_run: bool) -> None:
    """Install missing MAS or Scoop for the resolved platform using native installers."""
    for manager in (PkgManager.MAS, PkgManager.SCOOP):
        if manager not in managers or find_executable(manager, env=env):
            continue

        # Run the missing manager's installer directly.
        match manager:
            case PkgManager.MAS:
                run(["brew", "install", "mas"], env=env, dry_run=dry_run, check=True)
            case PkgManager.SCOOP:
                run(
                    "$installer = Invoke-RestMethod -Uri https://get.scoop.sh\n"
                    "& ([scriptblock]::Create($installer))",
                    env=env,
                    dry_run=dry_run,
                    check=True,
                )


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Install
# ═════════════════════════════════════════════════════════════════════════════


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
        case "winget":
            command = [
                "winget",
                "install",
                "--id",
                value,
                "--no-upgrade",
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
        check=source != "winget",
    )
    if result is None or source != "winget" or result.returncode == 0:
        return
    # APPINSTALLER_CLI_ERROR_PACKAGE_ALREADY_INSTALLED, including signed Windows exits.
    if result.returncode & 0xFFFFFFFF == 0x8A150061:
        return
    raise RuntimeError(f"Winget installation failed (exit {result.returncode}): {value}")


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Upgrade
# ═════════════════════════════════════════════════════════════════════════════


def upgrade_managers(managers: list[PkgManager], *, env: dict[str, str], dry_run: bool) -> None:
    """Upgrade and clean up all packages belonging to the resolved managers."""
    for manager in managers:
        match manager:
            case PkgManager.BREW:
                commands = [["brew", "update"], ["brew", "upgrade"]]
                if machine_env.PLATFORM == Platform.MAC:
                    commands.append(["brew", "upgrade", "--cask", "--greedy-latest"])
                commands.extend(
                    [
                        ["brew", "autoremove"],
                        ["brew", "cleanup", "--prune=all"],
                        ["brew", "services", "cleanup"],
                    ]
                )
            case PkgManager.MAS:
                commands = [["mas", "upgrade"]]
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


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Query
# ═════════════════════════════════════════════════════════════════════════════


def installed_packages(
    sources: set[PackageSource], *, env: dict[str, str]
) -> dict[PackageSource, set[str]]:
    """Query each selected manager once and return installed identities by source."""
    installed: dict[PackageSource, set[str]] = {source: set() for source in sources}

    # Homebrew returns both kinds together; retain aliases and tap-qualified identities.
    if sources.intersection({"brew", "cask"}):
        result = query(["brew", "info", "--json=v2", "--installed"], env=env)
        data = json.loads(result.stdout)
        installed["brew"] = set()
        installed["cask"] = set()
        for formula in data["formulae"]:
            names = {formula["name"], *formula.get("aliases", []), *formula.get("oldnames", [])}
            installed["brew"].update(names)
            installed["brew"].add(formula["full_name"])
            if formula.get("tap"):
                installed["brew"].update(f"{formula['tap']}/{name}" for name in names)
        for cask in data["casks"]:
            names = {cask["token"], *cask.get("old_tokens", [])}
            installed["cask"].update(names)
            installed["cask"].add(cask["full_token"])
            if cask.get("tap"):
                installed["cask"].update(f"{cask['tap']}/{name}" for name in names)

    # MAS and Scoop expose complete installed-package lists.
    if "mas" in sources:
        result = query(["mas", "list"], env=env)
        installed["mas"] = {line.split()[0] for line in result.stdout.splitlines() if line.strip()}
    if "scoop" in sources:
        result = query(["scoop", "export"], env=env)
        installed["scoop"] = {app["Name"].casefold() for app in json.loads(result.stdout)["apps"]}

    # WinGet exports matched IDs to a file; unmatched apps retain the native install check.
    if "winget" in sources:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "packages.json"
            query(
                [
                    "winget",
                    "export",
                    "--output",
                    str(path),
                    "--accept-source-agreements",
                    "--disable-interactivity",
                ],
                env=env,
                timeout=120,
            )
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        installed["winget"] = {
            package["PackageIdentifier"].casefold()
            for source in data["Sources"]
            for package in source["Packages"]
        }
    return installed
