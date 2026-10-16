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

    mapping.source.stat()
    same_file = target.exists() and target.samefile(mapping.source)
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
        _create_symlink(mapping.source, target, env=env)

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


def _create_symlink(source: Path, target: Path, *, env: dict[str, str]) -> None:
    if not is_windows:
        target.symlink_to(source, target_is_directory=source.is_dir())
        return

    # Create the link elevated so SSH can traverse it, but keep the invoking user as owner.
    owner = query(["whoami"], env=env).stdout.strip()
    run(
        [
            "gsudo",
            "--direct",
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(Path(__file__).with_name("symlink.ps1")),
            "-Source",
            str(source),
            "-Target",
            str(target),
            "-Owner",
            owner,
        ],
        env=env,
        dry_run=False,
        check=True,
    )


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
