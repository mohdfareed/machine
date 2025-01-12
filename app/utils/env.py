"""Machine configuration utilities."""

__all__ = ["load_env_vars"]

from pathlib import Path
from typing import Optional

from dotenv import dotenv_values

from .filesystem import create_temp_file
from .shell import OS_EXECUTABLE, Executable, Shell


def load_env_vars(
    env_file: Path, executable: Optional[Executable]
) -> dict[str, Optional[str]]:
    """Load the environment variables from a file."""
    if env_file.suffix == ".ps1":
        executable = Executable.PWSH

    shell = Shell(executable or OS_EXECUTABLE)
    suffix = ".ps1" if shell.executable == Executable.PWSH else ".sh"
    env_contents = env_file.read_text(suffix)

    env_file = create_temp_file()
    env_file.write_text(env_contents)
    gen_env_file = create_temp_file()

    # load the environment variables into a file
    if env_file.suffix == ".ps1":
        cmd = (
            f'. "{env_file}" ; Get-ChildItem env:* | '
            f'ForEach-Object {{ "$($_.Name)=$($_.Value)" }} | '
            f'Out-File -FilePath "{gen_env_file}" ;'
        )
    else:
        cmd = f"source '{env_file}' && env > '{gen_env_file}'"
    shell.execute(cmd)

    return dotenv_values(gen_env_file)
