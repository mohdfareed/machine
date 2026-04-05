"""Validation and file deployment."""

import logging
import os
from pathlib import Path

from machine.core import is_windows, settings
from machine.manifest import FileMapping, Module

logger = logging.getLogger(__name__)


def validate(modules: list[Module]) -> list[str]:
    """Validate resolved modules. Returns a list of errors."""
    errors: list[str] = []

    for mod in modules:
        for fm in mod.files:
            if not Path(fm.source).exists():
                errors.append(f"Module '{mod.name}' file source missing: {fm.source}")
        for script in mod.scripts:
            if not Path(script).exists():
                errors.append(f"Module '{mod.name}' script missing: {script}")

    return errors


def deploy_files(
    files: list[FileMapping],
    owners: dict[str, str] | None = None,
) -> tuple[int, list[tuple[str, str, str]]]:
    """Symlink all file mappings. Returns (count created, failures)."""
    created = 0
    failures: list[tuple[str, str, str]] = []
    for fm in files:
        src = Path(fm.source)
        tgt = Path(os.path.expandvars(fm.target)).expanduser()
        module = (owners or {}).get(fm.source, "?")
        if not src.exists():
            logger.warning("[%s] source not found: %s", module, src)
            failures.append((module, str(src), "source not found"))
            continue
        try:
            if _symlink(src, tgt):
                created += 1
        except OSError as exc:
            logger.error("[%s] failed to link %s → %s: %s", module, tgt, src, exc)
            failures.append((module, str(tgt), str(exc)))
    return created, failures


def _symlink(source: Path, target: Path) -> bool:
    """Create or update a link. Returns True if changed."""

    def _norm(path: Path) -> str:
        try:
            return os.path.normcase(str(path.resolve(strict=False)))
        except OSError:
            return os.path.normcase(str(path.absolute()))

    def _points_to_source(link_path: Path, src_path: Path) -> bool:
        try:
            return link_path.exists() and os.path.samefile(link_path, src_path)
        except OSError:
            pass

        try:
            link_target = link_path.readlink()
        except OSError:
            return False

        if not link_target.is_absolute():
            link_target = link_path.parent / link_target

        return _norm(link_target) == _norm(src_path)

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
        if not backup.exists() and not backup.is_symlink():
            return backup

        index = 1
        while True:
            candidate = path.with_suffix(path.suffix + f".backup.{index}")
            if not candidate.exists() and not candidate.is_symlink():
                return candidate
            index += 1

    if settings.dry_run:
        if (target.exists() or target.is_symlink()) and _points_to_source(target, source):
            return False
        logger.info("[dry-run] link %s → %s", target, source)
        return True

    target.parent.mkdir(parents=True, exist_ok=True)

    if (target.exists() or target.is_symlink()) and _points_to_source(target, source):
        logger.debug("OK: %s", target)
        return False

    if target.is_symlink():
        logger.info("Update: %s → %s", target, source)
        target.unlink()
    elif target.exists():
        backup = _backup_path(target)
        logger.info("Backup: %s → %s", target, backup)
        target.rename(backup)
    else:
        logger.info("Link: %s → %s", target, source)

    _create_link(source, target)
    return True
