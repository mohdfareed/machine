"""Host facts, selected machine variables, and saved selection."""

import ntpath
import os
import platform
import re
import sys
from pathlib import Path

from platformdirs import user_config_path
from platformdirs.unix import Unix

from app.models import Platform

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Host
# ═════════════════════════════════════════════════════════════════════════════

ROOT = Path(__file__).resolve().parents[1]
"""Repository containing this installation."""

SCRIPTS_ROOT = Path(__file__).resolve().parent / "scripts"
"""Directory containing the app scripts."""

PLATFORM: Platform
"""Current host platform."""

match sys.platform:
    case _platform if _platform.startswith("darwin"):
        PLATFORM = Platform.MAC
    case _platform if _platform.startswith("win"):
        PLATFORM = Platform.WIN
    case _ if "microsoft-standard" in platform.release().lower():
        PLATFORM = Platform.WSL
    case _:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")

is_macos = PLATFORM.is_a(Platform.MAC)
is_windows = PLATFORM.is_a(Platform.WIN)
is_wsl = PLATFORM.is_a(Platform.WSL)
is_unix = PLATFORM.is_a(Platform.UNIX)


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Machine Environment
# ═════════════════════════════════════════════════════════════════════════════


def config_dir() -> Path:
    """Return the app configuration directory shared with shell startup files."""
    return user_config_path("mc", appauthor=False) if is_windows else Unix("mc").user_config_path


def get_current_machine() -> str | None:
    """Read the saved machine ID independently of the inherited shell environment."""
    path = config_dir() / "machine"
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8").strip() or None


def save_machine(machine_id: str, values: dict[str, str]) -> None:
    """Save the selected machine and its literal environment for shell startup."""
    directory = config_dir()
    directory.mkdir(parents=True, exist_ok=True)

    # Write native assignments without evaluating declared values in either shell.
    powershell = []
    fish = []
    for name, value in values.items():
        # PowerShell also treats typographic apostrophes as string delimiters.
        quoted = value
        for quote in ("'", "\u2018", "\u2019", "\u201a", "\u201b"):
            quoted = quoted.replace(quote, quote * 2)

        powershell.append(f"$env:{name} = '{quoted}'\n")
        quoted = value.replace("\\", "\\\\").replace("'", "\\'")
        fish.append(f"set -gx {name} '{quoted}'\n")

    # Write literal shell assignments.
    (directory / "env.ps1").write_text("".join(powershell), encoding="utf-8", newline="\n")
    if not is_windows:
        (directory / "env.fish").write_text("".join(fish), encoding="utf-8", newline="\n")

    # Record the selection after both shell files are ready.
    (directory / "machine").write_text(f"{machine_id}\n", encoding="utf-8")


def build_env(machine_id: str, values: dict[str, str | Path]) -> dict[str, str]:
    """Validate declared variables and normalize paths without expanding their content."""
    env: dict[str, str] = {}
    for name, value in values.items():
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError(f"Invalid environment variable name: {name!r}")

        if "\0" in str(value):
            raise ValueError(f"Environment variable {name} contains a null character")
        env[name.upper() if is_windows else name] = str(value)

    # The selected identity always overrides a declaration or inherited shell value.
    env["MC_ID"] = machine_id
    return env


def system_env(overrides: dict[str, str] | None = None) -> dict[str, str]:
    """Apply explicit values over inherited and current registered host variables."""
    if sys.platform != "win32":
        return {**os.environ, **(overrides or {})}

    import winreg

    # Overlay registered values while retaining variables supplied by the caller.
    env = {name.upper(): value for name, value in os.environ.items()}
    paths: list[str] = []
    expandable: set[str] = set()
    for hive, key in (
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        ),
        (winreg.HKEY_CURRENT_USER, "Environment"),
    ):
        try:
            with winreg.OpenKey(hive, key) as handle:
                for index in range(winreg.QueryInfoKey(handle)[1]):
                    name, value, kind = winreg.EnumValue(handle, index)
                    if not isinstance(value, str):
                        continue

                    name = name.upper()
                    if name == "PATH":
                        paths.append(value)
                        continue

                    env[name] = value
                    expandable.discard(name)
                    if kind == winreg.REG_EXPAND_SZ:
                        expandable.add(name)

        # Ignore missing keys.
        except FileNotFoundError:
            continue

    # Apply selected values before expanding registered references to them.
    selected = {name.upper(): value for name, value in (overrides or {}).items()}
    env.update(selected)
    expandable.difference_update(selected)

    for name in expandable:
        env[name] = _expand_registered(env[name], env, {name})
    if "PATH" in selected:
        return env
    paths = [_expand_registered(path, env, set()) for path in paths]

    # Prefer registered directories and retain temporary caller-only PATH entries.
    paths.append(env.get("PATH", ""))
    directories: dict[str, str] = {}
    for path in paths:
        for directory in path.split(";"):
            if directory:
                directories.setdefault(ntpath.normcase(ntpath.normpath(directory)), directory)

    env["PATH"] = ";".join(directories.values())
    return env


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Environment Helpers
# ═════════════════════════════════════════════════════════════════════════════

_WINDOWS_REFERENCE = re.compile(r"%([^%]+)%")


def _expand_registered(value: str, env: dict[str, str], seen: set[str]) -> str:
    def _replace(match: re.Match[str]) -> str:
        name = match[1].upper()
        if name not in env or name in seen:
            return match[0]
        return _expand_registered(env[name], env, seen | {name})

    return _WINDOWS_REFERENCE.sub(_replace, value)
