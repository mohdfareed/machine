"""Run maintenance for the current machine."""

from pathlib import Path
from typing import Annotated

import typer

from app.cli.entry import complete_modules, get_current_machine, print_summary
from app.env import PLATFORM, build_env, settings
from app.logging import console, err_console
from app.ops.managers import validate_managers
from app.ops.packages import install_packages
from app.ops.scripts import filter_scripts, run_scripts
from app.shell import cache_sudo

# =============================================================================
# MARK: Update Command
# =============================================================================


def update(
    module_names: Annotated[
        list[str],
        typer.Argument(
            metavar="modules",
            help="Limit to the specified modules.",
            autocompletion=complete_modules,
        ),
    ] = [],
) -> None:
    """Run maintenance and update scripts for the current machine."""
    from app.machine import load_manifest, resolve_modules

    root = settings.home
    machine_id = get_current_machine()
    if not machine_id:
        err_console.print("[red]No machine selected.[/]")
        err_console.print("[dim]Run: mc apply -m <id>[/]")
        raise SystemExit(1)

    # Load the machine and select maintenance inputs.
    manifest = load_manifest(machine_id, root)
    validate_managers(manifest.pkg_managers)
    all_modules = resolve_modules(manifest.modules, root)

    if module_names:
        unknown = set(module_names) - {m.name for m in all_modules}
        if unknown:
            err_console.print(f"[red]Unknown modules: {', '.join(sorted(unknown))}[/]")
            err_console.print("[dim]Run mc show to inspect the machine's configured modules.[/]")
            raise SystemExit(1)

        active = [m for m in all_modules if m.name in set(module_names) or m.name == "core"]
        raw_scripts = [s for m in active for s in m.scripts]
        all_packages = [p for m in active for p in m.packages]
    else:
        raw_scripts = [s for m in all_modules for s in m.scripts] + manifest.scripts
        all_packages = [p for m in all_modules for p in m.packages] + manifest.packages

    up_scripts = [s for s in filter_scripts(raw_scripts) if Path(s).name.startswith("up_")]
    script_packages = [p for p in all_packages if p.script and p.applies_to(PLATFORM)]
    if not up_scripts and not script_packages:
        console.print("[dim]No update actions found.[/]")
        return

    # Resolve ownership and the shared script environment.
    owners: dict[str, str] = {}
    for m in all_modules:
        for s in m.scripts:
            owners[s] = m.name
        for p in m.packages:
            owners[p.name] = m.name

    for s in manifest.scripts:
        owners.setdefault(s, machine_id)
    for p in manifest.packages:
        owners.setdefault(p.name, machine_id)

    script_env = build_env(machine_id, root)
    script_env["MC_PACKAGE_MANAGERS"] = " ".join(manifest.pkg_managers)
    mode = "[dim](dry-run)[/] " if settings.dry_run else ""
    console.print(f"{mode}Updating [bold]{machine_id}[/]")

    # Re-run script-backed packages before maintenance scripts.
    cache_sudo()
    failures = install_packages(
        script_packages,
        manifest.pkg_managers,
        owners=owners,
        rerun_script_packages=True,
    )

    failures.extend(run_scripts(up_scripts, env=script_env, owners=owners))
    print_summary(failures, settings.log_file)
