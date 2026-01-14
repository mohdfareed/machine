"""Cross-platform script runner."""

from __future__ import annotations

import os
from pathlib import Path

from machine.core import (
    CODESPACES,
    LINUX,
    MACOS,
    UNIX,
    WINDOWS,
    WSL,
    debug,
    get_machine_root,
    info,
    is_dry_run,
    run,
)
from machine.state import (
    MachineState,
    load_state,
    mark_script_run,
    save_state,
    should_run_once,
)

# Script prefixes that require state tracking
ONCE_PREFIXES = ("once_",)
ONCHANGE_PREFIXES = ("onchange_",)
TRACKED_PREFIXES = ONCE_PREFIXES + ONCHANGE_PREFIXES


def collect_scripts(machine_id: str, phase: str | None = None) -> list[Path]:
    """Collect scripts from base and machine directories.

    Args:
        machine_id: The machine identifier
        phase: Optional phase filter (e.g., "before", "after", "once")
               If None, returns all non-prefixed scripts.
    """
    root = get_machine_root()
    base_scripts = root / "config" / "scripts"
    machine_scripts = root / "machines" / machine_id / "scripts"

    scripts: list[Path] = []

    for scripts_dir in [base_scripts, machine_scripts]:
        if not scripts_dir.exists():
            continue

        for script in sorted(scripts_dir.iterdir()):
            if script.is_dir():
                continue
            if not _is_executable_script(script):
                continue
            if not _matches_platform(script):
                continue
            if not _matches_phase(script, phase):
                continue

            scripts.append(script)

    return scripts


def _is_executable_script(path: Path) -> bool:
    """Check if a path is an executable script."""
    executable_extensions = {".sh", ".py", ".ps1"}
    return path.suffix.lower() in executable_extensions


def _matches_platform(script: Path) -> bool:
    """Check if a script matches the current platform."""
    suffixes = [s.lower() for s in script.suffixes]

    # Platform-specific filters
    if ".win" in suffixes and not WINDOWS:
        return False
    if ".linux" in suffixes and not LINUX:
        return False
    if ".macos" in suffixes and not MACOS:
        return False
    if ".wsl" in suffixes and not WSL:
        return False
    if ".codespaces" in suffixes and not CODESPACES:
        return False
    if ".unix" in suffixes and not UNIX:
        return False

    return True


def _matches_phase(script: Path, phase: str | None) -> bool:
    """Check if a script matches the requested phase."""
    name = script.name

    # Extract phase from script name
    has_prefix = any(
        name.startswith(p) for p in ("before_", "after_", "once_", "onchange_")
    )

    if phase is None:
        # No phase requested - return scripts without prefixes
        return not has_prefix

    # Check if script matches requested phase
    return name.startswith(f"{phase}_")


def execute_script(script: Path) -> None:
    """Execute a single script."""
    # Set executable permission on Unix
    if os.name == "posix" and not is_dry_run():
        os.chmod(script, 0o755)

    # Build command based on script type
    if script.suffix == ".py":
        import sys

        cmd = f"{sys.executable} {script}"
    elif script.suffix == ".ps1":
        if WINDOWS:
            cmd = f'powershell -ExecutionPolicy Bypass -File "{script}"'
        else:
            cmd = f'pwsh -File "{script}"'
    else:
        cmd = str(script)

    info(f"running: {script.name}")
    run(cmd, check=False)


def run_scripts(
    machine_id: str,
    phase: str | None = None,
    state: MachineState | None = None,
) -> None:
    """Run scripts for a machine and phase.

    Args:
        machine_id: The machine identifier
        phase: Script phase ("before", "after", "once", "onchange", or None)
        state: Optional state dict for tracking run-once scripts
    """
    scripts = collect_scripts(machine_id, phase)

    if not scripts:
        debug("scripts", f"no scripts for phase: {phase}")
        return

    info(f"running {len(scripts)} scripts (phase: {phase or 'default'})")

    for script in scripts:
        # Check if this is a tracked script
        is_tracked = any(script.name.startswith(p) for p in TRACKED_PREFIXES)

        if is_tracked and state is not None:
            if not should_run_once(script, state):
                continue

        execute_script(script)

        # Mark as run if tracked
        if is_tracked and state is not None:
            mark_script_run(script, state)


def run_all_scripts(machine_id: str) -> None:
    """Run all scripts in the correct order."""
    state = load_state()
    state["machine_id"] = machine_id

    # Phase order: before -> default -> once -> onchange -> after
    run_scripts(machine_id, "before", state)
    run_scripts(machine_id, None, state)  # No prefix
    run_scripts(machine_id, "once", state)
    run_scripts(machine_id, "onchange", state)
    run_scripts(machine_id, "after", state)

    save_state(state)
