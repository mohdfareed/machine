import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]


def open_path(path: Path) -> None:
    path = path.expanduser()
    if not path.exists():
        raise SystemExit(f"Path does not exist: {path}")

    if sys.platform.startswith("darwin"):
        subprocess.run(["open", str(path)], check=True)
        return
    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
        return
    subprocess.run(["xdg-open", str(path)], check=True)
