"""Execute selected scripts with their required interpreters."""

import sys
from pathlib import Path

from app.shell import run


def run_scripts(
    scripts: list[Path],
    *,
    env: dict[str, str],
    dry_run: bool,
) -> None:
    """Run selected scripts in order, stopping at the first failure."""
    for script in scripts:
        # Python uses this runtime; Unix scripts use their executable bit and shebang.
        cmd = [sys.executable, str(script)] if script.suffix.lower() == ".py" else [str(script)]
        run(
            cmd,
            env=env,
            dry_run=dry_run,
            check=True,
            powershell=script.suffix.lower() == ".ps1",
        )
