"""Shell command execution."""

import logging
import shutil
import subprocess

from machine.config import app_settings
from machine.platform import is_windows

logger = logging.getLogger(__name__)


def run(
    cmd: str,
    *,
    check: bool = True,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a shell command. Skipped in dry-run mode."""
    logger.debug("$ %s", cmd)

    if app_settings.dry_run:
        logger.info("[dry-run] %s", cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    exe = shutil.which("powershell.exe") if is_windows else None
    return subprocess.run(
        cmd,
        shell=True,
        check=check,
        executable=exe,
        text=True,
        capture_output=capture,
    )
