"""CLI metadata, invocation options, and shared argument callbacks."""

from dataclasses import dataclass
from importlib.metadata import distribution

import typer

from app.discovery import list_machines, list_modules
from app.env import get_current_machine

# =============================================================================
# MARK: Application
# =============================================================================

_distribution = distribution("machine")
NAME = _distribution.metadata["Name"]
VERSION = _distribution.metadata["Version"]
DESCRIPTION = _distribution.metadata["Summary"]
COMMAND = next(
    entry.name for entry in _distribution.entry_points if entry.group == "console_scripts"
)


@dataclass
class Options:
    """Options belonging to one CLI invocation."""

    debug: bool = False


# =============================================================================
# MARK: Argument Callbacks
# =============================================================================


def validate_machine(value: str | None) -> str | None:
    """Validate a machine ID and return its canonical casing."""
    if value is None:
        return None

    machine_ids = list_machines()
    for machine_id in machine_ids:
        if machine_id.casefold() == value.casefold():
            return machine_id

    choices = "|".join(machine_ids)
    raise typer.BadParameter(f"{value!r} is not one of: {choices}")


def complete_machines(incomplete: str) -> list[tuple[str, str]]:
    """Complete machine IDs using current discovery and saved selection."""
    selected = get_current_machine()
    return [
        (name, "(default)" if name == selected else "")
        for name in list_machines()
        if name.startswith(incomplete)
    ]


def complete_modules(incomplete: str) -> list[tuple[str, str]]:
    """Complete discovered module names."""
    return [(name, "") for name in list_modules() if name.startswith(incomplete)]
