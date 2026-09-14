"""Command execution, bounded queries, and execution environment preparation."""

import os
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path

from app import reporting
from app.env import ROOT, is_windows, system_env

# =============================================================================
# MARK: Run Commands and Queries
# =============================================================================


def run(
    cmd: str | list[str],
    *,
    env: dict[str, str],
    dry_run: bool,
    capture_output: bool = False,
    echo_output: bool = False,
    check: bool = False,
    powershell: bool = False,
) -> subprocess.CompletedProcess[bytes] | None:
    """Announce a command, then run it or skip its execution during a preview."""
    if isinstance(cmd, str):
        command = cmd
    else:
        command = subprocess.list2cmdline(cmd) if is_windows else shlex.join(cmd)
    display = command.replace(str(ROOT) + os.sep, "." + os.sep)
    reporting.command(display)
    if dry_run:
        return None

    # Prepare the current host environment before resolving commands or interpreters.
    environment = process_env(env)
    if powershell:
        if isinstance(cmd, str):
            raise ValueError("PowerShell file execution requires an argument list")
        environment = prepare_powershell_env(cmd[0], environment)

    # Preserve arguments and inherit the terminal unless the caller needs output.
    if is_windows and isinstance(cmd, str):
        result = _run_powershell(cmd, environment, capture_output)
    else:
        args = cmd if isinstance(cmd, str) else [_resolve_executable(cmd[0], environment), *cmd[1:]]
        result = subprocess.run(
            args,
            shell=isinstance(cmd, str),
            env=environment,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.STDOUT if capture_output else None,
        )

    # Replay inspected output without changing it, then preserve failure status.
    if echo_output and result.stdout:
        reporting.plain(result.stdout.decode(errors="replace"), end="")
    if check and result.returncode != 0:
        detail = ""
        if capture_output and not echo_output and result.stdout:
            detail = "\n" + result.stdout.decode(errors="replace").strip()
        raise RuntimeError(f"Command failed (exit {result.returncode}): {display}{detail}")
    return result


def query(
    cmd: list[str],
    *,
    env: dict[str, str],
    timeout: float = 30,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a silent, bounded read with current host variables and explicit overrides."""
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


# =============================================================================
# MARK: Prepare Execution Environments
# =============================================================================


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
    return shutil.which(name, path=process_env(env).get("PATH", ""))


def powershell_executable(env: dict[str, str], *, dry_run: bool = False) -> str:
    """Choose the platform's PowerShell interpreter without launching it in previews."""
    if dry_run:
        return "powershell.exe" if is_windows else "pwsh"
    return _powershell_executable(process_env(env))


def prepare_powershell_env(executable: str, env: dict[str, str]) -> dict[str, str]:
    """Add bundled modules to an already prepared environment for the chosen interpreter."""
    key = "PSModulePath"
    if is_windows:
        key = next((name for name in env if name.casefold() == key.casefold()), key)
    module_path = env.get(key)
    if module_path is None:
        result = subprocess.run(
            [
                executable,
                "-NoProfile",
                "-Command",
                "[Console]::OutputEncoding = [Text.UTF8Encoding]::new(); $env:PSModulePath",
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(f"PowerShell environment setup failed: {detail}")
        module_path = result.stdout.strip()

    paths = [str(_SCRIPTS_ROOT), *module_path.split(os.pathsep)]
    return {**env, key: os.pathsep.join(dict.fromkeys(path for path in paths if path))}


# =============================================================================
# MARK: Process Helpers
# =============================================================================

_SCRIPTS_ROOT = Path(__file__).parent / "scripts"
_ENVIRONMENT_SCRIPT = _SCRIPTS_ROOT / "environment.unix.sh"

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
    executable = shutil.which(name, path=env.get("PATH", ""))
    if executable is None:
        raise FileNotFoundError(f"Executable not found: {name}")
    return executable


def _powershell_executable(env: dict[str, str]) -> str:
    names = ("powershell.exe",) if is_windows else ("pwsh", "pwsh-preview")
    for name in names:
        executable = shutil.which(name, path=env.get("PATH", ""))
        if executable is not None:
            return executable

    # Windows PowerShell ships with Windows even when PATH omits its directory.
    system_root = next(
        (value for key, value in env.items() if key.casefold() == "systemroot"), None
    )
    if is_windows and system_root:
        path = Path(system_root) / "System32" / "WindowsPowerShell" / "v1.0" / names[0]
        if path.is_file():
            return str(path)
    raise FileNotFoundError(f"PowerShell executable not found: {' or '.join(names)}")


def _run_powershell(
    cmd: str,
    env: dict[str, str],
    capture_output: bool,
) -> subprocess.CompletedProcess[bytes]:
    executable = _powershell_executable(env)
    environment = prepare_powershell_env(executable, env)

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
            env=environment,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.STDOUT if capture_output else None,
        )
        result.args = cmd
        return result
