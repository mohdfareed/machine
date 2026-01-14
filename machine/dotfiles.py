"""Dotfiles symlink manager.

Handles symlinking configuration files from config/ to home directory,
with machine-specific overrides from machines/{id}/.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from machine.core import (
    MACOS,
    WINDOWS,
    WSL,
    debug,
    get_machine_root,
    info,
    is_dry_run,
)


def _vscode_path(filename: str) -> str:
    """Get platform-specific VSCode config path."""
    if MACOS:
        return f"Library/Application Support/Code/User/{filename}"
    elif WINDOWS:
        return f"AppData/Roaming/Code/User/{filename}"
    else:  # Linux/WSL
        return f".config/Code/User/{filename}"


class DotfileLink(NamedTuple):
    """A dotfile symlink to create."""

    source: Path  # Absolute path to source file
    target: Path  # Absolute path to symlink location
    is_override: bool  # True if from machine-specific config


def get_dotfile_mappings(machine_id: str) -> list[tuple[str, str]]:
    """Get dotfile mappings, can be extended per-machine if needed."""
    # Note: git config handled separately by link_git_config
    return [
        # Shell
        ("shell/zshrc", ".zshrc"),
        ("shell/zshenv", ".zshenv"),
        # Vim/Neovim
        ("vim", ".config/nvim"),
        # VSCode
        ("vscode/settings.json", _vscode_path("settings.json")),
        ("vscode/keybindings.json", _vscode_path("keybindings.json")),
        ("vscode/snippets", _vscode_path("snippets")),
        ("vscode/prompts", _vscode_path("prompts")),
        # SSH
        ("ssh.config", ".ssh/config"),
        # Ghostty (Unix only)
        ("ghostty.config", ".config/ghostty/config"),
    ]


def resolve_dotfile(
    config_path: str, machine_id: str
) -> tuple[Path, bool] | None:
    """Resolve a config path to its source, checking for machine override.

    Returns (source_path, is_override) or None if file doesn't exist.
    """
    root = get_machine_root()
    machine_source = root / "machines" / machine_id / config_path
    base_source = root / "config" / config_path

    if machine_source.exists():
        return (machine_source, True)
    elif base_source.exists():
        return (base_source, False)
    else:
        return None


def collect_dotfiles(machine_id: str) -> list[DotfileLink]:
    """Collect all dotfiles that need to be linked."""
    home = Path.home()
    links: list[DotfileLink] = []

    for config_path, home_path in get_dotfile_mappings(machine_id):
        resolved = resolve_dotfile(config_path, machine_id)
        if resolved is None:
            debug("dotfiles", f"not found, skipping: {config_path}")
            continue

        source, is_override = resolved
        target = home / home_path

        links.append(
            DotfileLink(source=source, target=target, is_override=is_override)
        )

    return links


def create_symlink(link: DotfileLink) -> bool:
    """Create a symlink, handling existing files.

    Returns True if link was created/updated, False if skipped.
    """
    source, target, is_override = link
    override_marker = " (override)" if is_override else ""

    # Ensure parent directory exists
    if not is_dry_run():
        target.parent.mkdir(parents=True, exist_ok=True)

    # Check if target already exists
    if target.is_symlink():
        current_target = target.resolve()
        if current_target == source.resolve():
            debug("dotfiles", f"already linked: {target}")
            return False
        # Remove old symlink
        info(f"updating link: {target}{override_marker}")
        if not is_dry_run():
            target.unlink()
    elif target.exists():
        # Target exists and is not a symlink - back it up
        backup = target.with_suffix(target.suffix + ".backup")
        info(f"backing up existing file: {target} -> {backup}")
        if not is_dry_run():
            target.rename(backup)
    else:
        info(f"linking: {target} -> {source}{override_marker}")

    # Create symlink
    if not is_dry_run():
        target.symlink_to(source)

    return True


def link_dotfiles(machine_id: str) -> int:
    """Link all dotfiles for a machine.

    Returns the number of links created/updated.
    """
    info(f"linking dotfiles for machine: {machine_id}")
    links = collect_dotfiles(machine_id)
    created = 0

    for link in links:
        if create_symlink(link):
            created += 1

    info(
        f"dotfiles: {created} created/updated, {len(links) - created} unchanged"
    )
    return created


def link_git_config(machine_id: str) -> None:
    """Link git config with platform-specific includes.

    Git config uses [include] directives, so we need to:
    1. Link base .gitconfig
    2. Link platform-specific override (if exists)
    3. Link machine-specific override (if exists)
    """
    root = get_machine_root()
    home = Path.home()

    # Determine platform suffix
    if WINDOWS and not WSL:
        platform_suffix = "windows"
    elif WSL:
        platform_suffix = "wsl"
    else:
        platform_suffix = None  # No platform-specific config for macOS/Linux

    # Link base gitconfig
    base_gitconfig = root / "config" / "git" / ".gitconfig"
    if base_gitconfig.exists():
        create_symlink(
            DotfileLink(
                source=base_gitconfig,
                target=home / ".gitconfig",
                is_override=False,
            )
        )

    # Link platform-specific gitconfig
    if platform_suffix:
        platform_gitconfig = (
            root / "config" / "git" / f".gitconfig.{platform_suffix}"
        )
        if platform_gitconfig.exists():
            create_symlink(
                DotfileLink(
                    source=platform_gitconfig,
                    target=home / f".gitconfig.{platform_suffix}",
                    is_override=False,
                )
            )

    # Link machine-specific gitconfig
    machine_gitconfig = root / "machines" / machine_id / ".gitconfig"
    if machine_gitconfig.exists():
        create_symlink(
            DotfileLink(
                source=machine_gitconfig,
                target=home / f".gitconfig.{machine_id}",
                is_override=True,
            )
        )

    # Link global gitignore
    gitignore = root / "config" / "git" / ".gitignore"
    if gitignore.exists():
        create_symlink(
            DotfileLink(
                source=gitignore,
                target=home / ".gitignore",
                is_override=False,
            )
        )
