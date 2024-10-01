"""Machine configuration files."""

import logging as _logging
import os as _os
from typing import Optional as _Optional

LOGGER = _logging.getLogger(__name__)
"""The machine configuration logger."""

# REVIEW: use Path(app_dir) / "config.json"

# Configuration files =========================================================

config = _os.path.dirname(_os.path.realpath(__file__))
vim = _os.path.join(config, "vim")
vscode = _os.path.join(config, "vscode")
gitconfig = _os.path.join(config, ".gitconfig")
gitignore = _os.path.join(config, ".gitignore")
ps_profile = _os.path.join(config, "ps_profile.ps1")
tmux = _os.path.join(config, "tmux.conf")
zed_settings = _os.path.join(config, "zed_settings.jsonc")
zshrc = _os.path.join(config, "zshrc")
zshenv = _os.path.join(config, "zshenv")

# Environment variables =======================================================

_env_file = ps_profile if _utils.is_windows() else zshenv
MACHINE = _utils.load_env_var(_env_file, "MACHINE") or _os.path.join(
    _os.path.expanduser("~"), ".machine"
)
private_env = (
    _utils.load_env_var(ps_profile if _utils.is_windows() else zshenv, "PRIVATE_ENV")
    or None
)
ssh_keys = (
    _utils.load_env_var(ps_profile if _utils.is_windows() else zshenv, "SSH_KEYS")
    or None
)
shell_completions = _utils.load_env_var(ps_profile, "COMPLETIONS_PATH") or None
del _env_file

# OS-specific environment variables ===========================================

xdg_config: _Optional[str] = None
xdg_data: _Optional[str] = None
local_data: _Optional[str] = None
app_data: _Optional[str] = None

if _utils.is_unix():
    xdg_config = _utils.load_env_var(zshenv, "XDG_CONFIG_HOME") or _os.path.join(
        _os.path.expanduser("~"), ".config"
    )
    xdg_data = _utils.load_env_var(zshenv, "XDG_DATA_HOME") or _os.path.join(
        _os.path.expanduser("~"), ".local", "share"
    )

if _utils.is_windows():
    local_data = _utils.load_env_var(ps_profile, "LOCALAPPDATA")
    app_data = _utils.load_env_var(ps_profile, "APPDATA")

# Helper functions ============================================================


def link_private_config(private_machine: str) -> None:
    """Load private machine configuration."""
    if not private_env or not ssh_keys:
        raise _core.SetupError("Private machine not configured.")

    LOGGER.info("Loading private machine configuration: %s", private_machine)
    source_env = _os.path.join(private_machine, _os.path.basename(private_env))
    source_keys = _os.path.join(private_machine, _os.path.basename(ssh_keys))

    try:  # symlink private environment
        _utils.symlink(source_env, private_env)
    except FileNotFoundError:
        LOGGER.warning("Private environment not found.")

    try:  # symlink SSH keys
        _utils.symlink(source_keys, ssh_keys)
    except FileNotFoundError:
        LOGGER.warning("SSH keys not found.")


def report(machine_config: _Optional[dict[str, str]]) -> None:
    """Report the machine configuration.
    Args:
        machine_config (dict[str, str]): Additional configuration."""

    LOGGER.debug("Machine configuration:")
    LOGGER.debug("\tOS: %s", _utils.OS)
    LOGGER.debug("\tArch: %s", _utils.ARCH)
    LOGGER.debug("\tMACHINE: %s", MACHINE)
    LOGGER.debug("\tPRIVATE_ENV: %s", private_env)
    LOGGER.debug("\tSSH_KEYS: %s", ssh_keys)

    if _utils.is_unix():
        LOGGER.debug("\tXDG_CONFIG_HOME: %s", xdg_config)
        LOGGER.debug("\tXDG_DATA_HOME: %s", xdg_data)

    if _utils.is_windows():
        LOGGER.debug("\tLOCALAPPDATA: %s", local_data)
        LOGGER.debug("\tAPPDATA: %s", app_data)

    if machine_config:
        LOGGER.debug("Additional configuration:")
        for key, value in machine_config.items():
            LOGGER.debug("\t%s: %s", key, value)
