"""Core log slicing logic: iterate lines and apply time-range + regex filters."""

import re
from datetime import datetime
from typing import Generator, IO, Optional

from logslice.parser import extract_timestamp, matches_filter


def slice_log(
    file_obj: IO[str],
    pattern: Optional[re.Pattern] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> Generator[str, None, None]:
    """
    Yield log lines that satisfy time-range and regex filter constraints.

    Args:
        file_obj: An open, readable text file object.
        pattern:  Compiled regex pattern to filter lines (None = no filter).
        start:    Inclusive start datetime (None = no lower bound).
        end:      Inclusive end datetime (None = no upper bound).
    """
    for line in file_obj:
        line = line.rstrip('\n')
        if not line:
            continue

        # Time-range filtering
        if start is not None or end is not None:
            ts = extract_timestamp(line)
            if ts is not None:
                if start is not None and ts < start:
                    continue
                if end is not None and ts > end:
                    continue
            # Lines with no parseable timestamp pass through when a range is set

        # Regex filtering
        if not matches_filter(line, pattern):
            continue

        yield line


def count_matches(
    file_obj: IO[str],
    pattern: Optional[re.Pattern] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> int:
    """Return the number of lines that match the given filters."""
    return sum(1 for _ in slice_log(file_obj, pattern=pattern, start=start, end=end))
