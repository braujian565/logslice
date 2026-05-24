"""
Bookmarker: named bookmark management for log positions.

Allows users to save and restore named positions (line offsets) within
log files, enabling fast re-entry at a previously marked location.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

_DEFAULT_DIR = Path.home() / ".logslice" / "bookmarks"


@dataclass
class Bookmark:
    name: str
    filepath: str
    offset: int
    line_number: int
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Bookmark":
        return Bookmark(**data)


def _bookmark_path(name: str, directory: Path) -> Path:
    safe = name.replace("/", "_").replace("\\", "_")
    return directory / f"{safe}.json"


def save_bookmark(bookmark: Bookmark, directory: Optional[Path] = None) -> Path:
    """Persist a bookmark to disk. Returns the path written."""
    d = Path(directory) if directory else _DEFAULT_DIR
    d.mkdir(parents=True, exist_ok=True)
    path = _bookmark_path(bookmark.name, d)
    path.write_text(json.dumps(bookmark.to_dict(), indent=2))
    return path


def load_bookmark(name: str, directory: Optional[Path] = None) -> Optional[Bookmark]:
    """Load a bookmark by name. Returns None if not found."""
    d = Path(directory) if directory else _DEFAULT_DIR
    path = _bookmark_path(name, d)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return Bookmark.from_dict(data)


def delete_bookmark(name: str, directory: Optional[Path] = None) -> bool:
    """Delete a bookmark. Returns True if deleted, False if not found."""
    d = Path(directory) if directory else _DEFAULT_DIR
    path = _bookmark_path(name, d)
    if path.exists():
        path.unlink()
        return True
    return False


def list_bookmarks(directory: Optional[Path] = None) -> list[Bookmark]:
    """Return all bookmarks in the directory, sorted by name."""
    d = Path(directory) if directory else _DEFAULT_DIR
    if not d.exists():
        return []
    results = []
    for p in sorted(d.glob("*.json")):
        try:
            results.append(Bookmark.from_dict(json.loads(p.read_text())))
        except (json.JSONDecodeError, TypeError, KeyError):
            continue
    return results


def read_from_bookmark(filepath: str, bookmark: Bookmark):
    """Yield lines from *filepath* starting at the bookmark's byte offset."""
    with open(filepath, "r", errors="replace") as fh:
        fh.seek(bookmark.offset)
        yield from fh
