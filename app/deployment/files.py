"""File deployment, preservation, and permissions."""

import subprocess
from pathlib import Path

from app.config.models import FileMapping
from app.runtime.env import ROOT, is_windows
from app.runtime.reporting import link
from app.runtime.shell import query, run

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Deployment
# ═════════════════════════════════════════════════════════════════════════════


def deploy_file(mapping: FileMapping, *, env: dict[str, str], dry_run: bool):
    """Deploy a resolved mapping and its permissions, preserving existing data."""
    target = mapping.target
    backup: Path | None = None
    same_file = target.exists() and target.samefile(mapping.source)

    mapping.source.stat()
    if dry_run:
        link(mapping.source, mapping.target, root=ROOT)
        return  # Dry run.
    if same_file:
        _set_permissions(mapping.source, target, mapping.mode, env=env)
        return  # Already deployed.

    try:  # Deploy the mapping, with backup and recovery.
        target.parent.mkdir(parents=True, exist_ok=True)

        # Deploy the file, backing up only *real* targets.
        if target.is_symlink():
            target.unlink()
        if target.exists(follow_symlinks=False):
            backup = _create_backup(target)
        target.symlink_to(mapping.source, target_is_directory=mapping.source.is_dir())

        # Apply declared permissions after creating the replacement link.
        _set_permissions(mapping.source, target, mapping.mode, env=env)
        link(mapping.source, mapping.target, root=ROOT)

    # Add recovery context only when existing data has moved to a backup.
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        if backup is None:
            raise
        raise OSError(
            f"Failed to deploy {target} -> {mapping.source}: {exc}. "
            f"Existing data is preserved at {backup}."
        ) from exc


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Backup
# ═════════════════════════════════════════════════════════════════════════════


def _create_backup(target: Path) -> Path:
    index = 1  # Generate a unique backup.
    backup = target.with_suffix(target.suffix + ".backup")
    while backup.exists() or backup.is_symlink():
        backup = target.with_suffix(target.suffix + f".backup.{index}")
        index += 1

    # Rename the existing target to the backup path, preserving its data.
    target.rename(backup)
    return backup


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Permissions
# ═════════════════════════════════════════════════════════════════════════════


def _set_permissions(source: Path, target: Path, mode: int | None, *, env: dict[str, str]) -> None:
    if mode is None:
        return
    source.chmod(mode)  # Symlink security requires restricting the source.

    # MARK: Windows
    # ─────────────────────────────────────────────────────────────────────────
    if not is_windows or mode & 0o077:
        return  # Skip group/other permissions.

    # Clear explicit grants as well as inherited access on owner-only mappings.
    user = query(["whoami"], env=env).stdout.strip()
    _restrict(source, user, env=env)
    if not target.is_symlink():
        return

    _restrict(target, user, env=env, link=True)


def _restrict(path: Path, user: str, *, env: dict[str, str], link: bool = False) -> None:
    suffix = ["/L"] if link else []
    for arguments in (
        ["/setowner", user],
        ["/reset"],
        ["/inheritance:r", "/grant:r", f"{user}:(F)", "*S-1-5-18:(F)"],
    ):
        run(
            ["icacls", str(path), *arguments, *suffix],
            env=env,
            dry_run=False,
            capture_output=True,
            check=True,
        )
