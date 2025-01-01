"""Shell commands execution."""

__all__ = ["Shell", "ShellResults", "ShellError", "Executable", "OS_EXECUTABLE"]

import logging
import os
import shutil
import subprocess
from enum import Enum
from typing import Any, NamedTuple, Optional, TypeVar

from rich.text import Text

LOGGER = logging.getLogger(__name__)
"""The shell logger."""
T = TypeVar("T")

# special log matching tokens
ERROR_TOKEN = "error"
SUDO_TOKEN = "sudo"

ShellResults = NamedTuple("ShellResults", [("returncode", int), ("output", str)])
"""Shell command results."""


class Executable(Enum):
    """Supported shell executables."""

    ZSH = shutil.which("zsh") or "zsh"
    BASH = shutil.which("bash") or "bash"
    SH = shutil.which("sh") or "sh"
    PWSH = shutil.which("pwsh") or shutil.which("powershell") or "powershell"
    WSL = shutil.which("wsl") or shutil.which("wsl") or "wsl"


IS_WINDOWS = os.name == (_ := "nt")  # whether the OS is Windows
OS_EXECUTABLE = Executable(
    shutil.which("zsh") or shutil.which("bash") or shutil.which("sh") or "sh"
    if not IS_WINDOWS
    else shutil.which("pwsh") or shutil.which("powershell") or "powershell.exe"
)
"""The default shell executable for the current OS."""


class Shell:  # pylint: disable=too-few-public-methods
    """Shell commands execution interface."""

    def __init__(
        self,
        executable: Executable = OS_EXECUTABLE,
        env: Optional[dict[str, Any]] = None,
    ) -> None:
        self.executable = executable
        self.env = env

    def execute(
        self, command: str, throws: bool = True, info: bool = False
    ) -> ShellResults:
        """Run a shell command and return its output and return code.

        Args:
            command: The command to run.
            throws: Whether to throw on non-zero return code.
            info: Wether to log debug messages as info.
        Returns:
            tuple[int, str]: The return code and output of the command.
        Raises:
            ShellError: If the command has a non-zero return code and `throws` is True.
        """

        LOGGER.debug("[bold]Executing command:[/] [blue]%s[/]", command)
        if SUDO_TOKEN in command.lower() and not IS_WINDOWS:
            LOGGER.warning("[bold yellow]Running sudo command[/]")

        with _create_process(command, self.env, self.executable) as process:
            results = _exec_process(process, info)

        if throws and results.returncode != 0:
            LOGGER.error("Command failed: [%d] %s", results.returncode, results.output)
            raise ShellError(results)
        return results


def _create_process(
    command: str, env: Optional[dict[str, Any]], executable: Executable
) -> subprocess.Popen[str]:
    sub_proc = None

    if executable == Executable.PWSH:
        sub_proc = subprocess.Popen(  # pylint: disable=consider-using-with
            [executable.value, "-Command", command],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

    elif executable == Executable.WSL:
        sub_proc = subprocess.Popen(  # pylint: disable=consider-using-with
            [executable.value, "-e", "bash", "-c", f"'{command}'"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

    else:  # default to unix shell
        sub_proc = subprocess.Popen(  # pylint: disable=consider-using-with
            command,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            executable=executable.value,
            shell=True,
            text=True,
        )

    return sub_proc


class ShellError(Exception):
    """Exception due to a shell error."""


def _exec_process(process: subprocess.Popen[str], info: bool = False) -> ShellResults:
    output = ""  # if the process has no output
    if process.stdout is None:
        raise ShellError("Process output file not found.")

    while True:  # read output from the process in real time
        line = process.stdout.readline().strip()
        output += line

        if line:  # log the line
            _log_line(Text.from_markup(line).plain, info)

        # break if process is done
        if process.poll() is not None:
            break
    return ShellResults(process.wait(), Text.from_markup(output.strip()).plain)


def _log_line(line: str, info: bool) -> None:
    if ERROR_TOKEN in line.lower():
        LOGGER.error("[italic]%s[/]", line)
    elif info:
        LOGGER.info("[italic]%s[/]", line)
    else:
        LOGGER.debug("[italic]%s[/]", line)


if IS_WINDOWS:
    Shell().execute(
        "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force"
    )
