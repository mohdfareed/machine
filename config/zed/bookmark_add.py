#!/usr/bin/env -S uv run --script
"""Toggle a Zed bookmark entry for the current cursor location."""

import sys
from pathlib import Path


def _usage() -> int:
    print("usage: bookmark_add.py worktree_root relative_file row column", file=sys.stderr)
    return 1


def _read_label(source_file: Path, row: int, location: str) -> str:
    if row < 1 or not source_file.is_file():
        return location

    try:
        line = source_file.read_text(encoding="utf-8", errors="replace").splitlines()[row - 1]
    except IndexError:
        return location

    stripped = line.strip()
    return stripped or location


def _load_entries(bookmark_file: Path) -> list[tuple[str, str]]:
    if not bookmark_file.is_file():
        return []

    blocks = bookmark_file.read_text(encoding="utf-8").split("\n\n")
    entries: list[tuple[str, str]] = []
    for block in blocks:
        lines = [line for line in block.splitlines() if line.strip()]
        if len(lines) >= 2:
            entries.append((lines[0], lines[1]))
    return entries


def _save_entries(bookmark_file: Path, entries: list[tuple[str, str]]) -> None:
    if not entries:
        bookmark_file.unlink(missing_ok=True)
        return

    content = "\n\n".join(f"{label}\n{location}" for label, location in entries) + "\n"
    bookmark_file.write_text(content, encoding="utf-8")


def main(argv: list[str]) -> int:
    if len(argv) != 5:
        return _usage()

    worktree_root, relative_file, row_text, column_text = argv[1:]

    try:
        row = int(row_text)
        column = int(column_text)
    except ValueError:
        return _usage()

    worktree = Path(worktree_root)
    bookmark_dir = worktree / ".zed"
    bookmark_file = bookmark_dir / "bookmarks.txt"
    location = f"{relative_file}:{row - 1}:{column - 1}"

    bookmark_dir.mkdir(parents=True, exist_ok=True)

    entries = _load_entries(bookmark_file)
    kept_entries = [
        (label, saved_location) for label, saved_location in entries if saved_location != location
    ]
    if len(kept_entries) != len(entries):
        _save_entries(bookmark_file, kept_entries)
        return 0

    label = _read_label(worktree / relative_file, row, location)
    kept_entries.append((label, location))
    _save_entries(bookmark_file, kept_entries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
