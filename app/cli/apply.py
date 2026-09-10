"""Deploy the selected machine configuration."""

from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer

from app import reporting
from app.cli.entry import (
    complete_machines,
    complete_modules,
    get_current_machine,
    machines,
    save_current_machine,
)
from app.env import build_env, settings, write_env_file
from app.machine import validate_modules
from app.ops.files import deploy_files
from app.ops.managers import validate_managers
from app.ops.packages import install_packages
from app.ops.scripts import filter_scripts, run_scripts
from app.shell import cache_sudo

if TYPE_CHECKING:
    from app.models import Failure, Machine, Module

# =============================================================================
# MARK: Apply Command
# =============================================================================


def apply(
    machine: Annotated[
        str | None,
        typer.Option(
            "-m",
            "--machine",
            metavar="MACHINE",
            help=f"The machine to set up. <{'|'.join(machines.choices)}>",
            autocompletion=complete_machines,
            click_type=machines,
            prompt=True,
        ),
    ] = get_current_machine() or None,
    module_names: Annotated[
        list[str],
        typer.Argument(
            metavar="modules",
            help="Limit setup to the specified modules.",
            autocompletion=complete_modules,
        ),
    ] = [],
) -> None:
    """Deploy configs, install packages, and run scripts."""
    from app.machine import load_manifest, resolve_modules

    root = settings.home
    if not machine:
        reporting.error("No machine selected.")
        reporting.detail("Run: mc apply -m <id>", error=True)
        raise SystemExit(1)

    # Load and validate the machine configuration.
    manifest = load_manifest(machine, root)
    validate_managers(manifest.pkg_managers)
    save_current_machine(machine)
    write_env_file(machine, root)
    all_modules = resolve_modules(manifest.modules, root)
    module_filter = set(module_names)
    errors = validate_modules(all_modules)

    if errors:
        reporting.error("Invalid module configuration.")
        for e in errors:
            reporting.detail(e, error=True)
        reporting.detail("Fix the module configuration, then run: mc apply", error=True)
        raise SystemExit(1)

    # Select deployment inputs, keeping core setup in filtered runs.
    if module_filter:
        unknown = module_filter - {m.name for m in all_modules}
        if unknown:
            reporting.error(f"Unknown modules: {', '.join(sorted(unknown))}")
            reporting.detail("Run mc show to inspect the machine's configured modules.", error=True)
            raise SystemExit(1)

        active = [m for m in all_modules if m.name in module_filter or m.name == "core"]
        all_files = [f for m in active for f in m.files]
        all_packages = [p for m in active for p in m.packages]
        raw_scripts = [s for m in active for s in m.scripts]
    else:
        active = all_modules
        all_files = [f for m in active for f in m.files] + manifest.files
        all_packages = [p for m in active for p in m.packages] + manifest.packages
        raw_scripts = [s for m in active for s in m.scripts] + manifest.scripts

    # Prepare the script environment and execution phases.
    all_scripts = filter_scripts(raw_scripts)
    script_env = build_env(machine, root)
    script_env["MC_PACKAGE_MANAGERS"] = " ".join(manifest.pkg_managers)
    owners = _build_owners(active, manifest, machine)

    reporting.heading(f"Apply plan · {machine}" if settings.dry_run else f"Applying {machine}")
    reporting.detail(f"Modules: {', '.join(m.name for m in active)}")

    init_scripts = [s for s in all_scripts if Path(s).name.startswith("init_")]
    post_scripts = [
        s
        for s in all_scripts
        if not Path(s).name.startswith("init_") and not Path(s).name.startswith("up_")
    ]

    # Deploy files and run setup before installing packages.
    cache_sudo()
    failures: list[Failure] = []

    reporting.heading("Deploying files")
    file_result = deploy_files(all_files, owners=owners)
    reporting.detail(
        f"{file_result.created} files would change"
        if settings.dry_run
        else f"{file_result.created} files changed"
    )
    failures.extend(file_result.failures)
    init_failures = run_scripts(init_scripts, env=script_env, owners=owners)
    failures.extend(init_failures)

    if init_failures:
        reporting.print_summary(failures, settings.log_file, action="Apply", init_failed=True)
        return

    # Install packages and run the remaining apply scripts.
    failures.extend(install_packages(all_packages, manifest.pkg_managers, owners=owners))
    failures.extend(run_scripts(post_scripts, env=script_env, owners=owners))

    reporting.print_summary(failures, settings.log_file, action="Apply")


# =============================================================================
# MARK: Helpers
# =============================================================================


def _build_owners(
    active_modules: list["Module"],
    manifest: "Machine",
    machine_id: str,
) -> dict[str, str]:
    # Assign module ownership to files, packages, and scripts.
    owners: dict[str, str] = {}
    for m in active_modules:
        for s in m.scripts:
            owners[s] = m.name
        for f in m.files:
            owners[f.source] = m.name
        for p in m.packages:
            owners[p.name] = m.name

    # Fill in machine-owned entries without replacing module ownership.
    for f in manifest.files:
        owners.setdefault(f.source, machine_id)
    for p in manifest.packages:
        owners.setdefault(p.name, machine_id)
    for s in manifest.scripts:
        owners.setdefault(s, machine_id)
    return owners
