"""State tracking for run-once operations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TypedDict

from src.core import debug, get_machine_root

STATE_FILE = Path.home() / ".machine-state.json"


class ScriptState(TypedDict):
    """State for a tracked script."""

    hash: str
    last_run: str  # ISO format


class MachineState(TypedDict):
    """Full state file structure."""

    machine_id: str
    scripts: dict[str, ScriptState]


def load_state() -> MachineState:
    """Load state from disk, or return empty state."""
    if not STATE_FILE.exists():
        return {"machine_id": "", "scripts": {}}

    try:
        data = json.loads(STATE_FILE.read_text())
        return data
    except (json.JSONDecodeError, KeyError):
        debug("state", f"corrupted state file, resetting: {STATE_FILE}")
        return {"machine_id": "", "scripts": {}}


def save_state(state: MachineState) -> None:
    """Save state to disk."""
    STATE_FILE.write_text(json.dumps(state, indent=2))
    debug("state", f"saved state to {STATE_FILE}")


def get_script_hash(script: Path) -> str:
    """Get SHA256 hash of a script file."""
    content = script.read_bytes()
    return hashlib.sha256(content).hexdigest()[:16]


def should_run_once(script: Path, state: MachineState) -> bool:
    """Check if a run-once script should execute.

    Returns True if:
    - Script has never run
    - Script content has changed (for onchange_ scripts)
    """
    script_key = str(script.relative_to(get_machine_root()))
    current_hash = get_script_hash(script)

    if script_key not in state["scripts"]:
        debug("state", f"script not in state, will run: {script_key}")
        return True

    stored = state["scripts"][script_key]

    # For onchange scripts, check if content changed
    if script.name.startswith("onchange_"):
        if stored["hash"] != current_hash:
            debug("state", f"script changed, will run: {script_key}")
            return True
        debug("state", f"script unchanged, skipping: {script_key}")
        return False

    # For once scripts, never re-run
    debug("state", f"once script already run, skipping: {script_key}")
    return False


def mark_script_run(script: Path, state: MachineState) -> None:
    """Mark a script as having been run."""
    from datetime import datetime, timezone

    script_key = str(script.relative_to(get_machine_root()))
    state["scripts"][script_key] = {
        "hash": get_script_hash(script),
        "last_run": datetime.now(timezone.utc).isoformat(),
    }
    debug("state", f"marked as run: {script_key}")
