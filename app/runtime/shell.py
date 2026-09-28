"""Command execution, bounded queries, and execution environment preparation."""

import os
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.runtime import reporting
from app.runtime.env import ROOT, is_windows, system_env

_ENVIRONMENT_SCRIPT = Path(__file__).with_name("environment.sh")


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Run Commands and Queries
# ═════════════════════════════════════════════════════════════════════════════


def run(
    cmd: str | list[str],
    *,
    env: dict[str, str],
    dry_run: bool,
    capture_output: bool = False,
    check: bool = False,
    powershell: bool = False,
) -> subprocess.CompletedProcess[bytes] | None:
    """Run or preview a command; powershell lists contain a script path and its arguments."""
    if powershell:
        if isinstance(cmd, str):
            raise ValueError("PowerShell file execution requires an argument list")
        cmd = ["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", *cmd]
    if isinstance(cmd, str):
        command = cmd
    else:
        command = subprocess.list2cmdline(cmd) if is_windows else shlex.join(cmd)

    reporting.command(command, root=ROOT)
    if dry_run:
        return None

    # Prepare the current host environment before resolving commands or interpreters.
    environment = process_env(env)

    # Preserve arguments and inherit the terminal unless the caller needs output.
    if is_windows and isinstance(cmd, str):
        result = _run_powershell(
            cmd, _powershell_executable(environment), environment, capture_output
        )
    else:
        args = cmd
        if isinstance(cmd, list):
            executable = (
                _powershell_executable(environment)
                if powershell
                else _resolve_executable(cmd[0], environment)
            )
            args = [executable, *cmd[1:]]
        result = subprocess.run(
            args,
            shell=isinstance(cmd, str),
            env=environment,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.STDOUT if capture_output else None,
        )

    # Preserve failure status and include captured diagnostics when available.
    if check:
        if capture_output and result.returncode != 0:
            detail = "\n" + result.stdout.decode(errors="replace").strip() if result.stdout else ""
            raise RuntimeError(f"Command failed (exit {result.returncode}): {command}{detail}")
        result.check_returncode()

    reporting.command_end(result.returncode)
    return result


def query(
    cmd: list[str],
    *,
    env: dict[str, str],
    timeout: float = 30,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a silent, bounded read with current host variables and explicit overrides."""
    command = subprocess.list2cmdline(cmd) if is_windows else shlex.join(cmd)
    reporting.debug(f"Query: {command}")
    environment = process_env(env)
    result = subprocess.run(
        [_resolve_executable(cmd[0], environment), *cmd[1:]],
        env=environment,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Query failed (exit {result.returncode}): {cmd[0]}\n{detail}")
    return result


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Prepare Execution Environments
# ═════════════════════════════════════════════════════════════════════════════


def process_env(overrides: dict[str, str]) -> dict[str, str]:
    """Prepare current host variables and command activation, then apply explicit overrides."""
    # Keep a parent Git hook or diff tool from redirecting commands to its repository.
    environment = _without_git_context(system_env(overrides))
    if is_windows:
        return environment

    # Activate installed commands in a bounded shell without loading user profiles.
    result = subprocess.run(
        [
            "/bin/sh",
            "-c",
            'set -e; . "$1" >&2; /usr/bin/env -0',
            "mc environment",
            str(_ENVIRONMENT_SCRIPT),
        ],
        env=environment,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode(errors="replace").strip()
        raise RuntimeError(f"Environment setup failed (exit {result.returncode}): {detail}")

    # NUL separation preserves multiline values; selected-machine values remain authoritative.
    environment = dict(
        os.fsdecode(value).split("=", 1) for value in result.stdout.split(b"\0") if b"=" in value
    )
    environment.update(overrides)
    return _without_git_context(environment)


def find_executable(name: str, *, env: dict[str, str]) -> str | None:
    """Find a command using the same prepared environment as execution."""
    executable = shutil.which(name, path=process_env(env).get("PATH", ""))
    reporting.debug(f"Executable {name}: {executable or 'not found'}")
    return executable


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Process Helpers
# ═════════════════════════════════════════════════════════════════════════════


# Repository-local variables listed by `git rev-parse --local-env-vars`.
# Keep global configuration, identity and SSH settings; discard diff-tool callbacks too.
_GIT_CONTEXT_VARIABLES = {
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CONFIG",
    "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_COUNT",
    "GIT_OBJECT_DIRECTORY",
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_IMPLICIT_WORK_TREE",
    "GIT_GRAFT_FILE",
    "GIT_INDEX_FILE",
    "GIT_NO_REPLACE_OBJECTS",
    "GIT_REPLACE_REF_BASE",
    "GIT_PREFIX",
    "GIT_SHALLOW_FILE",
    "GIT_COMMON_DIR",
    "GIT_EXEC_PATH",
    "GIT_EXTERNAL_DIFF",
}


def _without_git_context(env: dict[str, str]) -> dict[str, str]:
    return {
        name: value
        for name, value in env.items()
        if name.upper() not in _GIT_CONTEXT_VARIABLES
        and not name.upper().startswith(("GIT_DIFF_", "GIT_DIFFTOOL_"))
    }


def _resolve_executable(name: str, env: dict[str, str]) -> str:
    # Windows shell=False does not use the supplied environment's PATH for lookup.
    if is_windows:
        return shutil.which(name, path=env.get("PATH", "")) or name
    return name


def _powershell_executable(env: dict[str, str]) -> str:
    names = ("pwsh.exe", "powershell.exe") if is_windows else ("pwsh",)
    for name in names:
        executable = shutil.which(name, path=env.get("PATH", ""))
        if executable is not None:
            return executable

    # Windows PowerShell ships with Windows even when PATH omits its directory.
    system_root = next(
        (value for key, value in env.items() if key.casefold() == "systemroot"), None
    )
    if is_windows and system_root:
        path = Path(system_root) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
        if path.is_file():
            return str(path)
    raise FileNotFoundError(f"PowerShell executable not found: {' or '.join(names)}")


def _run_powershell(
    cmd: str,
    executable: str,
    env: dict[str, str],
    capture_output: bool,
) -> subprocess.CompletedProcess[bytes]:
    # Use -File to preserve source quoting and relay plain text and native exits.
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".ps1", encoding="utf-8-sig", delete_on_close=False
    ) as script:
        script.write(
            "try {\n" + cmd + "\nif (-not $?) {\n"
            "if ($LASTEXITCODE) { exit $LASTEXITCODE }\nexit 1\n}\n}\n"
            "catch {\n[Console]::Error.WriteLine($_.Exception.Message)\nexit 1\n}\n"
        )
        script.close()
        result = subprocess.run(
            [executable, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script.name],
            env=env,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.STDOUT if capture_output else None,
        )
        result.args = cmd
        return result
