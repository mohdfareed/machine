"""File deployment and permissions."""

import logging
import os
import stat
import subprocess
from pathlib import Path

from app import reporting
from app.env import PLATFORM, is_windows, settings
from app.models import Failure, FileMapping, FileResult

_logger = logging.getLogger(__name__)

# =============================================================================
# MARK: File Deployment
# =============================================================================


def deploy_files(
    files: list[FileMapping],
    owners: dict[str, str] | None = None,
) -> FileResult:
    """Deploy applicable file mappings and return the created count and failures."""
    reporting.heading("Deploying files")
    created = 0
    failures: list[Failure] = []

    # Skip inapplicable mappings and missing sources before deployment.
    for fm in files:
        if not fm.applies_to(PLATFORM):
            _logger.debug("Skip: %s", fm.target)
            continue

        src = Path(fm.source)
        tgt = Path(os.path.expandvars(fm.target)).expanduser()
        module = (owners or {}).get(fm.source, "?")
        if not src.exists():
            reporting.error(f"[{module}] Source not found: {src}")
            failures.append(Failure(module=module, item=str(src), detail="source not found"))
            continue

        try:
            if _symlink(src, tgt, fm.mode):
                created += 1
        except OSError as exc:
            reporting.error(f"[{module}] Failed to link {tgt}")
            _logger.debug("[%s] Failed to link %s → %s: %s", module, tgt, src, exc, exc_info=True)
            failures.append(Failure(module=module, item=str(tgt), detail=str(exc)))

    results = FileResult(created=created, failures=failures)
    reporting.detail(f"{results.created} files changed")
    return results


# =============================================================================
# MARK: Link Management
# =============================================================================


def _symlink(source: Path, target: Path, mode: int | None = None) -> bool:
    # Preview link changes without touching the filesystem.
    if settings.dry_run:
        if _points_to_source(target, source):
            return False
        reporting.detail(f"Would link {target} → {source}")
        return True

    # Refresh permissions when the target already points to the source.
    target.parent.mkdir(parents=True, exist_ok=True)
    if _points_to_source(target, source):
        changed = _set_permissions(source, target, mode)
        _logger.debug("OK: %s", target)
        return changed

    # Remove stale links or preserve existing files before replacement.
    if target.is_symlink():
        _logger.info("Update: %s → %s", target, source)
        target.unlink()
    elif target.exists():
        backup = _backup_path(target)
        _logger.info("Backup: %s → %s", target, backup)
        target.rename(backup)
    else:
        _logger.info("Link: %s → %s", target, source)

    # Create the link and apply the requested permissions.
    _create_link(source, target)
    _set_permissions(source, target, mode)
    return True


def _points_to_source(link_path: Path, src_path: Path) -> bool:
    try:
        return link_path.exists() and os.path.samefile(link_path, src_path)
    except OSError:
        pass

    # Compare link paths when filesystem identity cannot be queried.
    try:
        link_target = link_path.readlink()
    except OSError:
        return False

    if not link_target.is_absolute():
        link_target = link_path.parent / link_target

    return _norm(link_target) == _norm(src_path)


def _norm(path: Path) -> str:
    try:
        return os.path.normcase(str(path.resolve(strict=False)))
    except OSError:
        return os.path.normcase(str(path.absolute()))


def _create_link(src_path: Path, dst_path: Path) -> None:
    try:
        dst_path.symlink_to(src_path, target_is_directory=src_path.is_dir())
    except OSError as exc:
        if is_windows and getattr(exc, "winerror", None) == 1314:
            raise OSError(
                "Symlink creation failed - enable Developer Mode first.\n"
                "Settings → System → For developers → Developer Mode"
            ) from exc
        raise


def _backup_path(path: Path) -> Path:
    backup = path.with_suffix(path.suffix + ".backup")
    index = 1
    while backup.exists() or backup.is_symlink():
        backup = path.with_suffix(path.suffix + f".backup.{index}")
        index += 1
    return backup


# =============================================================================
# MARK: Permissions
# =============================================================================


def _set_permissions(source: Path, target: Path, mode: int | None) -> bool:
    if mode is None:
        return False

    # Apply the source mode before restricting owner-only Windows mappings.
    changed = not is_windows and stat.S_IMODE(source.stat().st_mode) != mode
    source.chmod(mode)
    if not is_windows or mode & 0o077:
        return changed

    # Restrict the source to the current user and SYSTEM.
    user = subprocess.run(
        ["whoami"],
        capture_output=True,
        check=True,
        text=True,
    ).stdout.strip()
    _restrict(source, user)
    if not target.is_symlink():
        return changed

    # Recreate the link if its existing ACL prevents restriction.
    try:
        _restrict(target, user, link=True)
    except OSError:
        target.unlink()
        _create_link(source, target)
        _restrict(target, user, link=True)
        changed = True

    return changed


def _restrict(path: Path, user: str, *, link: bool = False) -> None:
    suffix = ["/L"] if link else []
    try:
        subprocess.run(
            ["icacls", path, "/setowner", user, *suffix],
            capture_output=True,
            check=True,
            text=True,
        )
        subprocess.run(
            [
                "icacls",
                path,
                "/inheritance:r",
                "/grant:r",
                f"{user}:(F)",
                "*S-1-5-18:(F)",
                *suffix,
            ],
            capture_output=True,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise OSError(exc.stderr.strip() or f"Failed to set permissions on {path}") from exc
