"""Current-machine persistence helpers."""

from machine.core import settings

_MACHINE_FILE = settings.app_dir / "machine.txt"


def get_current_machine() -> str | None:
    """Return the last-used machine ID, or None if not set."""
    return _MACHINE_FILE.read_text().strip() if _MACHINE_FILE.exists() else None


def save_current_machine(machine_id: str) -> None:
    """Persist the current machine ID."""
    _MACHINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _MACHINE_FILE.write_text(machine_id)
