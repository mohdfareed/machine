"""File deployment, preservation, and permissions."""

import os
import stat
import subprocess
from pathlib import Path

from app.env import is_windows
from app.models import FileMapping
from app.shell import query, run

# ═════════════════════════════════════════════════════════════════════════════
# MARK: Deploy a File
# ═════════════════════════════════════════════════════════════════════════════


def deploy_file(mapping: FileMapping, *, env: dict[str, str], dry_run: bool) -> Path | None:
    """Deploy a resolved mapping and return its changed target, preserving existing data."""
    source = Path(mapping.source)
    target = Path(mapping.target)
    backup: Path | None = None
    if not source.exists():
        raise FileNotFoundError(f"Source not found: {source}")

    # Inspect live identity and permissions before the preview boundary.
    same_source = _points_to_source(target, source)
    permissions_changed = mapping.mode is not None and (
        is_windows or stat.S_IMODE(source.stat().st_mode) != mapping.mode
    )

    # Preserve existing file if no changed detected or in dry-run mode.
    if same_source and not permissions_changed:
        return None
    if dry_run:
        return target

    try:  # Fix permissions and deploy the mapping, with backup and recovery.
        if same_source:
            _set_permissions(source, target, mapping.mode, env=env)
            return target

        # Preserve a *real* target before replacing it with the configured link.
        # This assumes symlinks are safe to overwrite, which is true for me.
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists(follow_symlinks=False) and not target.is_symlink():
            destination = _backup_path(target)
            target.rename(destination)
            backup = destination
        _create_link(source, target)

        # Apply declared permissions after creating the replacement link.
        if not permissions_changed:
            return target
        _set_permissions(source, target, mapping.mode, env=env)
        return target

    # Report failures with recovery instructions and preserve existing data when possible.
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        recovery = f" Existing data is preserved at {backup}." if backup is not None else ""
        if not target.exists() and not target.is_symlink():
            recovery += f" Recreate the link {target} → {source} after resolving the failure."
        raise OSError(f"Failed to deploy {target} → {source}: {exc}.{recovery}") from exc


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Inspect and Create Links
# ═════════════════════════════════════════════════════════════════════════════


def _points_to_source(target: Path, source: Path) -> bool:
    try:  # Compare filesystem identity when available.
        return target.exists() and os.path.samefile(target, source)
    except OSError:
        pass

    try:  # Compare normalized link paths.
        linked = target.readlink()
    except OSError:
        return False

    # Compare the resolved link path to the source path.
    if not linked.is_absolute():
        linked = target.parent / linked  # Account for relative links.
    return os.path.normcase(str(linked.resolve())) == os.path.normcase(str(source.resolve()))


def _create_link(source: Path, target: Path) -> None:
    try:  # Create a symlink to the source, overwriting any existing link or file.
        target.symlink_to(source, target_is_directory=source.is_dir())
    except OSError as exc:
        if is_windows and getattr(exc, "winerror", None) == 1314:
            raise OSError(
                "Symlink creation requires Developer Mode. "
                "Enable it in Settings → System → For developers."
            ) from exc
        raise


def _backup_path(target: Path) -> Path:
    index = 1  # Generate a unique backup.
    backup = target.with_suffix(target.suffix + ".backup")
    while backup.exists() or backup.is_symlink():
        backup = target.with_suffix(target.suffix + f".backup.{index}")
        index += 1
    return backup


# ═════════════════════════════════════════════════════════════════════════════
# MARK: Apply Permissions
# ═════════════════════════════════════════════════════════════════════════════


def _set_permissions(source: Path, target: Path, mode: int | None, *, env: dict[str, str]) -> None:
    if mode is None:
        return
    source.chmod(mode)
    if not is_windows or mode & 0o077:
        return

    # Clear explicit grants as well as inherited access on owner-only mappings.
    user = query(["whoami"], env=env).stdout.strip()
    _restrict(source, user, env=env)
    if not target.is_symlink():
        return

    # Recreate an existing link when its old ACL prevents resetting it.
    try:
        _restrict(target, user, env=env, link=True)
    except OSError, RuntimeError:
        target.unlink()
        _create_link(source, target)
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
