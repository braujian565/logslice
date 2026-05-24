"""
Bookmark reporter: format bookmark listings for plain-text and JSON output.
"""

from __future__ import annotations

import json
from typing import List

from logslice.bookmarker import Bookmark


def format_bookmark_plain(bookmark: Bookmark) -> str:
    """Single-line human-readable representation of a bookmark."""
    return (
        f"[{bookmark.name}] {bookmark.filepath} "
        f"@ line {bookmark.line_number} (offset {bookmark.offset}) "
        f"saved {bookmark.created_at}"
    )


def format_bookmark_json(bookmark: Bookmark) -> str:
    """JSON representation of a bookmark."""
    return json.dumps(bookmark.to_dict())


def format_bookmark_list_plain(bookmarks: List[Bookmark]) -> str:
    """Format a list of bookmarks as a plain-text table."""
    if not bookmarks:
        return "No bookmarks saved."
    lines = ["Saved bookmarks:", "-" * 60]
    for bm in bookmarks:
        lines.append(format_bookmark_plain(bm))
    return "\n".join(lines)


def format_bookmark_list_json(bookmarks: List[Bookmark]) -> str:
    """Format a list of bookmarks as a JSON array."""
    return json.dumps([bm.to_dict() for bm in bookmarks], indent=2)


def report_bookmarks(
    bookmarks: List[Bookmark],
    fmt: str = "plain",
) -> str:
    """Dispatch to the correct formatter based on *fmt*."""
    if fmt == "json":
        return format_bookmark_list_json(bookmarks)
    return format_bookmark_list_plain(bookmarks)
