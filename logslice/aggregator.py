"""Log line aggregation: group and count lines by pattern or time bucket."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Iterable, Iterator, Optional

from logslice.parser import extract_timestamp


def aggregate_by_pattern(
    lines: Iterable[str],
    pattern: re.Pattern,
    group: int = 0,
) -> dict[str, int]:
    """Count occurrences of each captured group (or full match) across lines.

    Args:
        lines: Iterable of raw log lines.
        pattern: Compiled regex to match against each line.
        group: Capture group index to use as the bucket key (0 = full match).

    Returns:
        Mapping of matched text -> occurrence count, sorted descending.
    """
    counts: Counter[str] = Counter()
    for line in lines:
        m = pattern.search(line)
        if m:
            try:
                key = m.group(group)
            except IndexError:
                key = m.group(0)
            counts[key] += 1
    return dict(counts.most_common())


def aggregate_by_time_bucket(
    lines: Iterable[str],
    bucket_seconds: int = 60,
) -> dict[str, int]:
    """Count log lines per time bucket.

    Lines whose timestamp cannot be parsed are placed in an '__unknown__' bucket.

    Args:
        lines: Iterable of raw log lines.
        bucket_seconds: Width of each time bucket in seconds.

    Returns:
        Mapping of ISO-8601 bucket start -> line count, sorted chronologically.
    """
    if bucket_seconds <= 0:
        raise ValueError("bucket_seconds must be a positive integer")

    delta = timedelta(seconds=bucket_seconds)
    counts: dict[str, int] = defaultdict(int)

    for line in lines:
        ts = extract_timestamp(line)
        if ts is None:
            counts["__unknown__"] += 1
        else:
            # Floor to nearest bucket
            epoch = datetime(1970, 1, 1)
            total_seconds = int((ts - epoch).total_seconds())
            bucket_start_epoch = (total_seconds // bucket_seconds) * bucket_seconds
            bucket_dt = epoch + timedelta(seconds=bucket_start_epoch)
            counts[bucket_dt.strftime("%Y-%m-%dT%H:%M:%S")] += 1

    # Sort chronologically, unknown last
    unknown = counts.pop("__unknown__", None)
    result = dict(sorted(counts.items()))
    if unknown is not None:
        result["__unknown__"] = unknown
    return result


def top_n(
    aggregated: dict[str, int],
    n: int,
) -> dict[str, int]:
    """Return the top-N entries from an aggregated result."""
    if n <= 0:
        raise ValueError("n must be a positive integer")
    return dict(list(aggregated.items())[:n])
