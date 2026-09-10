"""Shell environment preparation, terminal streaming, and file logging."""

import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from app import reporting
from app.env import is_unix, is_windows, settings

_REPO_ROOT = Path(__file__).resolve().parents[1]
_logger = logging.getLogger(__name__)
_output_logger = logging.getLogger("app.logging.output")

# Strip ANSI/DEC escape sequences for log-file output.
_ANSI_RE = re.compile(r"\x1b(?:\[[0-9;?]*[A-Za-z]|\][^\x07]*\x07|\([A-Z])")


# =============================================================================
# MARK: Prepare Shell Environment
# =============================================================================

_sudo_keepalive: threading.Event | None = None


def cache_sudo() -> None:
    """Prompt for sudo once and keep credentials alive in the background."""
    global _sudo_keepalive

    if is_windows or settings.dry_run or _sudo_keepalive is not None:
        return

    # Acquire credentials before starting background refreshes.
    rc = subprocess.call(["sudo", "-v"], stdin=sys.stdin)
    if rc != 0:
        reporting.warning(f"sudo authentication failed (exit {rc}); scripts may prompt again.")
        return

    stop = threading.Event()
    _sudo_keepalive = stop

    def _keepalive() -> None:
        while not stop.wait(60):
            subprocess.call(["sudo", "-v"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    threading.Thread(target=_keepalive, daemon=True).start()


def refresh_path() -> None:
    """Refresh PATH from the Windows registry or a Unix login shell."""
    # Equivalent to `is_windows` but is a statically known platform guard.
    if sys.platform == "win32":
        import winreg

        paths = [os.environ.get("PATH", "")]
        for hive, key in (
            (
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
            ),
            (winreg.HKEY_CURRENT_USER, "Environment"),
        ):
            try:
                with winreg.OpenKey(hive, key) as handle:
                    value, _ = winreg.QueryValueEx(handle, "Path")
                    paths.append(os.path.expandvars(value))
            except OSError:
                pass

        # Deduplicate directories, not whole PATH strings, so repeated refreshes cannot grow PATH.
        entries = (entry for path in paths for entry in path.split(os.pathsep) if entry)
        unique: dict[str, str] = {}
        for entry in entries:
            unique.setdefault(os.path.normcase(os.path.normpath(entry)), entry)

        os.environ["PATH"] = os.pathsep.join(unique.values())
        return

    # Import the login-shell PATH on Unix.
    try:
        shell = os.environ.get("SHELL", "/bin/sh")
        out = subprocess.check_output([shell, "-lc", "echo $PATH"], text=True, timeout=5).strip()

        if out:
            os.environ["PATH"] = out
            _logger.debug("Refreshed PATH: %s", out)
    except Exception as exc:
        _logger.debug("PATH refresh failed: %s", exc)

    # Include Homebrew even when the login shell has not configured it yet.
    for directory in ("/opt/homebrew/bin", "/usr/local/bin", "/home/linuxbrew/.linuxbrew/bin"):
        if not (Path(directory) / "brew").is_file():
            continue

        os.environ["PATH"] = directory + os.pathsep + os.environ.get("PATH", "")
        break


# =============================================================================
# MARK: Command Execution
# =============================================================================


def run(
    cmd: str,
    *,
    env: dict[str, str] | None = None,
    label: str = "",
    capture_output: bool = False,
) -> subprocess.CompletedProcess[bytes]:
    """Run a command, stream and log output, and optionally return it as bytes."""

    reporting.command(_short(cmd))
    if settings.dry_run:
        return subprocess.CompletedProcess(cmd, 0, stdout=b"" if capture_output else None)

    # Stream the command through the platform's transport.
    merged_env = {**os.environ, **(env or {})}
    if is_unix:
        rc, collected = _tee_pty(cmd, merged_env)
    else:
        rc, collected = _tee_pipe(cmd, merged_env)

    # Log captured output line by line without ANSI escapes.
    prefix = f"[{label}] " if label else ""
    for line in collected.decode(errors="replace").splitlines():
        stripped = _ANSI_RE.sub("", line).rstrip()
        if stripped:
            _output_logger.debug("%s| %s", prefix, stripped)

    return subprocess.CompletedProcess(cmd, rc, stdout=bytes(collected) if capture_output else None)


def _short(cmd: str) -> str:
    return cmd.replace(str(_REPO_ROOT) + os.sep, "").replace(str(_REPO_ROOT), ".")


# =============================================================================
# MARK: Unix Transport
# =============================================================================


def _tee_pty(cmd: str, env: dict[str, str]) -> tuple[int, bytearray]:
    if sys.platform == "win32":
        raise RuntimeError("_tee_pty is unavailable on Windows")

    import pty
    import select

    # Attach command output to a pseudo-terminal.
    primary, replica = pty.openpty()
    proc = subprocess.Popen(
        cmd,
        shell=True,
        env=env,
        stdin=sys.stdin,
        stdout=replica,
        stderr=replica,
    )
    os.close(replica)  # The parent does not write to the replica side.

    # Stream and collect output, closing the primary even on failure.
    collected = bytearray()
    try:
        while True:
            ready, _, _ = select.select([primary], [], [], 0.1)
            if ready:
                try:
                    chunk = os.read(primary, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                sys.stdout.buffer.write(chunk)
                sys.stdout.buffer.flush()
                collected.extend(chunk)
            elif proc.poll() is not None:
                # Drain remaining output after the process exits.
                while True:
                    try:
                        chunk = os.read(primary, 4096)
                    except OSError:
                        break
                    if not chunk:
                        break
                    sys.stdout.buffer.write(chunk)
                    sys.stdout.buffer.flush()
                    collected.extend(chunk)
                break
    finally:
        os.close(primary)

    proc.wait()
    return proc.returncode, collected


# =============================================================================
# MARK: Windows Transport
# =============================================================================


def _tee_pipe(cmd: str, env: dict[str, str]) -> tuple[int, bytearray]:
    if sys.platform != "win32":
        raise RuntimeError("_tee_pipe is only available on Windows")

    # Prefer PowerShell Core, falling back to Windows PowerShell.
    exe = shutil.which("pwsh.exe") or shutil.which("powershell.exe")
    if exe is None:
        raise FileNotFoundError("Failed to find PowerShell executable")

    # Use -File to preserve quoting and emit plain text instead of EncodedCommands.
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".ps1", encoding="utf-8-sig", delete_on_close=False
    ) as script:
        script.write(
            "try {\n" + cmd + "\nif (-not $?) { exit 1 }\n}\n"
            "catch {\n[Console]::Error.WriteLine($_.Exception.Message)\nexit 1\n}\n"
        )
        script.close()

        # Merge both output streams for terminal display and logging.
        proc = subprocess.Popen(
            [exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script.name],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        assert proc.stdout is not None

        # Stream and collect output before waiting for the exit status.
        collected = bytearray()
        while True:
            chunk = os.read(proc.stdout.fileno(), 4096)
            if not chunk:
                break
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
            collected.extend(chunk)

        proc.wait()
        return proc.returncode, collected
