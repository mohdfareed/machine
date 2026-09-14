"""Execute selected scripts with their required interpreters."""

import os
import sys
from pathlib import Path

from app.env import is_unix
from app.shell import powershell_executable, run


def run_scripts(
    scripts: list[str],
    *,
    env: dict[str, str],
    dry_run: bool,
) -> None:
    """Run selected scripts in order, stopping at the first failure."""
    for script in (Path(path) for path in scripts):
        powershell = script.suffix.lower() == ".ps1"

        # Select the interpreter and prepare only the environment it needs.
        match script.suffix.lower():
            case ".py":
                cmd = [sys.executable, str(script)]
            case ".ps1":
                executable = powershell_executable(env, dry_run=dry_run)
                cmd = [executable, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)]
            case _:
                cmd = [str(script)]
                if is_unix and not dry_run and not os.access(script, os.X_OK):
                    script.chmod(0o755)

        # Let execution prepare the environment and any required PowerShell modules.
        run(cmd, env=env, dry_run=dry_run, check=True, powershell=powershell)
