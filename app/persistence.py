"""Current-machine persistence helpers."""

from app.core import settings


def get_current_machine() -> str | None:
    """Return the last-used machine ID, or None if not set."""
    return settings.machine_file.read_text().strip() if settings.machine_file.exists() else None


def save_current_machine(machine_id: str) -> None:
    """Persist the current machine ID."""
    settings.machine_file.parent.mkdir(parents=True, exist_ok=True)
    settings.machine_file.write_text(machine_id)
