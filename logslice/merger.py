"""Merge multiple sorted log streams into a single chronologically ordered stream."""

from __future__ import annotations

import heapq
from typing import Iterable, Iterator, List, Optional, Tuple

from logslice.parser import extract_timestamp


def _keyed(lines: Iterable[str], source_index: int) -> Iterator[Tuple]:
    """Yield (timestamp_or_none, source_index, line) tuples for heap ordering."""
    for line in lines:
        ts = extract_timestamp(line)
        # Use a large sentinel so lines without timestamps sort last
        sort_key = ts.isoformat() if ts is not None else "\xff"
        yield (sort_key, source_index, line)


def merge_logs(
    sources: List[Iterable[str]],
    deduplicate: bool = False,
) -> Iterator[str]:
    """Merge multiple log line iterables into chronological order.

    Args:
        sources: A list of iterables, each yielding log lines (already roughly
                 sorted by time within each source).
        deduplicate: When True, consecutive identical lines are suppressed.

    Yields:
        Log lines in ascending timestamp order across all sources.
    """
    if not sources:
        return

    iterators = [
        _keyed(src, idx) for idx, src in enumerate(sources)
    ]

    heap: list = []
    for it in iterators:
        try:
            item = next(it)
            heapq.heappush(heap, (item, it))
        except StopIteration:
            pass

    last_line: Optional[str] = None

    while heap:
        (sort_key, source_index, line), it = heapq.heappop(heap)

        if not deduplicate or line != last_line:
            yield line
            last_line = line

        try:
            item = next(it)
            heapq.heappush(heap, (item, it))
        except StopIteration:
            pass


def merge_files(
    paths: List[str],
    deduplicate: bool = False,
    encoding: str = "utf-8",
) -> Iterator[str]:
    """Open multiple log files and merge their lines chronologically.

    Args:
        paths: File paths to open and merge.
        deduplicate: Suppress consecutive duplicate lines.
        encoding: File encoding (default utf-8).

    Yields:
        Merged log lines in chronological order.

    Raises:
        FileNotFoundError: If any of the given paths do not exist.
        PermissionError: If any of the given paths cannot be opened for reading.
    """
    handles = []
    try:
        for p in paths:
            handles.append(open(p, "r", encoding=encoding))
        yield from merge_logs(
            [h for h in handles],
            deduplicate=deduplicate,
        )
    finally:
        for h in handles:
            h.close()
