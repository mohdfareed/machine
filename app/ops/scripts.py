"""Execute selected scripts with their required interpreters."""

import os
import shlex
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
                cmd = _unix_command(script) if is_unix else [str(script)]
                if is_unix and not dry_run and not os.access(script, os.X_OK):
                    script.chmod(0o755)

        # Let execution prepare the environment and any required PowerShell modules.
        run(cmd, env=env, dry_run=dry_run, check=True, powershell=powershell)


def _unix_command(script: Path) -> list[str]:
    # Read the declared interpreter without executing it or loading shell configuration.
    with script.open(encoding="utf-8") as source:
        shebang = source.readline()
    if not shebang.startswith("#!"):
        return [str(script)]
    command = shlex.split(shebang[2:])
    if not command:
        return [str(script)]

    # Recognize direct interpreters and the usual env / env -S shebang forms.
    interpreter = 0
    if Path(command[0]).name == "env":
        interpreter = 2 if command[1:2] == ["-S"] else 1
    if len(command) <= interpreter or Path(command[interpreter]).name != "zsh":
        return [str(script)]

    # Keep declared options, then disable user startup files before the script path.
    position = command.index("--") if "--" in command else len(command)
    command.insert(position, "-f")
    return [*command, str(script)]
