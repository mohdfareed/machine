"""Validation and file deployment."""

import logging
import os
from pathlib import Path

from machine.core import settings
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
    """Create or update a symlink. Returns True if changed."""

    def _norm(path: Path) -> str:
        try:
            return os.path.normcase(str(path.resolve(strict=False)))
        except OSError:
            return os.path.normcase(str(path.absolute()))

    def _points_to_source(link_path: Path, src_path: Path) -> bool:
        try:
            link_target = link_path.readlink()
        except OSError:
            return False

        if not link_target.is_absolute():
            link_target = link_path.parent / link_target

        return _norm(link_target) == _norm(src_path)

    if settings.dry_run:
        if target.is_symlink() and _points_to_source(target, source):
            return False
        logger.info("[dry-run] link %s → %s", target, source)
        return True

    target.parent.mkdir(parents=True, exist_ok=True)

    if target.is_symlink():
        if _points_to_source(target, source):
            logger.debug("OK: %s", target)
            return False
        logger.info("Update: %s → %s", target, source)
        target.unlink()
    elif target.exists():
        backup = target.with_suffix(target.suffix + ".backup")
        logger.info("Backup: %s → %s", target, backup)
        target.rename(backup)
    else:
        logger.info("Link: %s → %s", target, source)

    target.symlink_to(source)
    return True
