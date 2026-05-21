"""Deduplication utilities for log lines."""

import hashlib
from collections import OrderedDict
from typing import Iterable, Iterator, Optional


def _line_key(line: str, ignore_timestamps: bool = False) -> str:
    """Compute a deduplication key for a line.

    If ignore_timestamps is True, attempt to strip leading timestamp-like
    prefixes before hashing so that the same message at different times
    is considered a duplicate.
    """
    text = line.rstrip("\n")
    if ignore_timestamps:
        # Strip common timestamp prefixes: ISO-8601, syslog, nginx bracket
        import re
        text = re.sub(
            r"^(?:"
            r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?|"  # ISO
            r"\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+\S+|"  # syslog
            r"\[\d{2}/\w+/\d{4}:\d{2}:\d{2}:\d{2}\s[+-]\d{4}\]"  # nginx
            r")\s*",
            "",
            text,
        )
    return hashlib.md5(text.encode("utf-8", errors="replace")).hexdigest()


def deduplicate_lines(
    lines: Iterable[str],
    ignore_timestamps: bool = False,
    max_cache: Optional[int] = None,
) -> Iterator[str]:
    """Yield only the first occurrence of each unique log line.

    Args:
        lines: Iterable of raw log line strings.
        ignore_timestamps: When True, timestamp prefixes are stripped before
            comparing lines so identical messages at different times collapse.
        max_cache: Maximum number of keys to keep in the seen-set.  When the
            cache is full the oldest entry is evicted (LRU-style).  None means
            unbounded.

    Yields:
        Unique lines in original order.
    """
    seen: "OrderedDict[str, None]" = OrderedDict()
    for line in lines:
        key = _line_key(line, ignore_timestamps=ignore_timestamps)
        if key in seen:
            continue
        seen[key] = None
        if max_cache is not None and len(seen) > max_cache:
            seen.popitem(last=False)
        yield line


def count_duplicates(
    lines: Iterable[str],
    ignore_timestamps: bool = False,
) -> dict:
    """Return a dict mapping each unique line key to its occurrence count.

    Useful for summary/statistics reporting.
    """
    counts: dict = {}
    for line in lines:
        key = _line_key(line, ignore_timestamps=ignore_timestamps)
        counts[key] = counts.get(key, 0) + 1
    return counts
