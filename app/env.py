"""Host facts, selected machine variables, and saved selection."""

import ntpath
import os
import re
import shutil
import sys
from pathlib import Path

from app.models import Platform

# =============================================================================
# MARK: Host
# =============================================================================

ROOT = Path(__file__).resolve().parents[1]
"""Repository containing this installation."""

PLATFORM: Platform
"""Current host platform."""

match sys.platform:
    case _ if sys.platform.startswith("linux") and shutil.which("wslinfo"):
        PLATFORM = Platform.WSL
    case _platform if _platform.startswith("darwin"):
        PLATFORM = Platform.MACOS
    case _platform if _platform.startswith("linux"):
        PLATFORM = Platform.LINUX
    case _platform if _platform.startswith("win"):
        PLATFORM = Platform.WINDOWS
    case _:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")

is_macos = PLATFORM.is_a(Platform.MACOS)
is_linux = PLATFORM.is_a(Platform.LINUX)
is_windows = PLATFORM.is_a(Platform.WINDOWS)
is_wsl = PLATFORM.is_a(Platform.WSL)
is_unix = PLATFORM.is_a(Platform.UNIX)


# =============================================================================
# MARK: Machine Environment
# =============================================================================


def get_current_machine() -> str | None:
    """Read the saved machine ID independently of the inherited shell environment."""
    return _read_env(_ENV_FILE, {}).get("MC_ID") or None


def set_current_machine(machine_id: str) -> None:
    """Save the selected machine and base variables for login shells."""
    values = _machine_values(machine_id)
    contents = "\n".join(f'{key}="{value}"' for key, value in values.items()) + "\n"
    _ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    _ENV_FILE.write_text(contents, encoding="utf-8")


def resolve_path(value: str, env: dict[str, str]) -> Path:
    """Expand a configured path using the selected environment and require an absolute path."""
    # Expand references before resolving the current user's home directory.
    variables = {**os.environ, **env}
    expanded = _expand(value, variables)
    if reference := _ENV_REFERENCE.search(expanded):
        raise ValueError(f"Unresolved path variable: {reference.group(0)}")

    if expanded == "~" or expanded.startswith(("~/", "~\\")):
        home = variables.get("USERPROFILE") if is_windows else variables.get("HOME")
        expanded = str(Path(home or Path.home()) / expanded[2:])

    path = Path(expanded)
    if not path.is_absolute():
        raise ValueError(f"Configured path must be absolute: {value}")
    return path


def build_env(machine_id: str, *, include_private: bool = True) -> dict[str, str]:
    """Build explicit machine overrides, using inherited values only for expansion."""
    # Resolve committed values without retaining unrelated inherited variables.
    base = _machine_values(machine_id)
    env = {**base, **_read_env(Path(base["MC_MACHINE"]) / "machine.env", {**os.environ, **base})}
    for key in ("MC_HOME", "MC_ID", "MC_MACHINE"):
        env[key] = base[key]
    env["MC_PRIVATE"] = str(resolve_path(env["MC_PRIVATE"], env))
    if not include_private:
        return env

    # Load this machine's secrets without letting them relocate its base paths.
    selected = {key: env[key] for key in base}
    private_file = Path(env["MC_PRIVATE"]) / "env" / f"{machine_id}.env"
    env.update(_read_env(private_file, {**os.environ, **env}))
    env.update(selected)
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


# =============================================================================
# MARK: Environment Helpers
# =============================================================================

_ENV_FILE = Path.home() / ".env"
_ENV_REFERENCE = re.compile(
    r"\$(?:{(?P<braced>[A-Za-z_][A-Za-z0-9_]*)}|(?P<plain>[A-Za-z_][A-Za-z0-9_]*))"
    r"|%(?P<windows>[A-Za-z_][A-Za-z0-9_]*)%"
)
_WINDOWS_REFERENCE = re.compile(r"%([^%]+)%")


def _machine_values(machine_id: str) -> dict[str, str]:
    return {
        "MC_HOME": str(ROOT),
        "MC_ID": machine_id,
        "MC_MACHINE": str(ROOT / "machines" / machine_id),
        "MC_PRIVATE": str(ROOT / "private"),
    }


def _read_env(path: Path, base: dict[str, str]) -> dict[str, str]:
    env = dict(base)
    if not path.is_file():
        return {}

    # Read plain dotenv assignments, preserving references for the expansion pass.
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        key, separator, value = line.partition("=")
        if not key.strip() or not separator:
            continue

        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]

        name = key.strip().upper() if is_windows else key.strip()
        values[name] = value
    env.update(values)

    # Resolve references within this file without rewriting inherited shell values.
    for _ in range(len(values)):
        changed = False
        for key in values:
            expanded = _expand(env[key], env)

            if expanded != env[key]:
                env[key] = expanded
                changed = True

        if not changed:
            break
    return {key: env[key] for key in values}


def _expand_registered(value: str, env: dict[str, str], seen: set[str]) -> str:
    def _replace(match: re.Match[str]) -> str:
        name = match[1].upper()
        if name not in env or name in seen:
            return match[0]
        return _expand_registered(env[name], env, seen | {name})

    return _WINDOWS_REFERENCE.sub(_replace, value)


def _expand(value: str, env: dict[str, str]) -> str:
    # Windows environment variable names are case-insensitive.
    variables = {key.casefold(): val for key, val in env.items()} if is_windows else env

    def _replace(match: re.Match[str]) -> str:
        name = next(group for group in match.groups() if group is not None)
        return variables.get(name.casefold() if is_windows else name, match.group(0))

    return _ENV_REFERENCE.sub(_replace, value)
