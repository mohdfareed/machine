"""Package installation."""

import logging
import shutil

from machine.manifest import Package
from machine.shell import run

logger = logging.getLogger(__name__)


def install_packages(packages: list[Package]) -> None:
    """Install packages using available managers."""
    if not packages:
        return

    managers = {
        name
        for name in ("brew", "apt", "snap", "winget", "scoop", "mas")
        if shutil.which(name)
    }
    logger.info("Managers: %s", ", ".join(sorted(managers)) or "none")

    for pkg in packages:
        _install(pkg, managers)


def _install(pkg: Package, managers: set[str]) -> None:
    """Install a single package."""
    for mgr, val in _sources(pkg, managers):
        if mgr == "script":
            logger.info("%s: script", pkg.name)
            run(val, check=False)
            return
        logger.info("%s: %s", pkg.name, mgr)
        run(_cmd(mgr, val), check=False)
        return

    logger.warning("No manager for: %s", pkg.name)


def _sources(pkg: Package, managers: set[str]) -> list[tuple[str, str]]:
    """Resolve available install sources, priority ordered."""
    opts: list[tuple[str, str]] = []
    if pkg.brew and "brew" in managers:
        opts.append(("brew", pkg.brew))
    if pkg.apt and "apt" in managers:
        opts.append(("apt", pkg.apt))
    if pkg.snap and "snap" in managers:
        opts.append(("snap", pkg.snap))
    if pkg.winget and "winget" in managers:
        opts.append(("winget", pkg.winget))
    if pkg.scoop and "scoop" in managers:
        opts.append(("scoop", pkg.scoop))
    if pkg.mas is not None and "mas" in managers:
        opts.append(("mas", str(pkg.mas)))
    if pkg.script:
        opts.append(("script", pkg.script))
    return opts


def _cmd(manager: str, value: str) -> str:
    """Build install command for a manager."""
    match manager:
        case "brew":
            return f"brew install {value}"
        case "apt":
            return f"sudo apt install -y {value}"
        case "snap":
            return f"sudo snap install {value}"
        case "winget":
            return (
                "winget install --accept-source-agreements "
                f"--accept-package-agreements {value}"
            )
        case "scoop":
            return f"scoop install {value}"
        case "mas":
            return f"mas install {value}"
        case _:
            raise ValueError(f"Unknown manager: {manager}")
