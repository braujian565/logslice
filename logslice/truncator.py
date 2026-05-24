"""Line truncation utilities for logslice."""

from __future__ import annotations

from typing import Iterable, Iterator

DEFAULT_MAX_LENGTH = 512
DEFAULT_SUFFIX = "..."


def truncate_line(line: str, max_length: int = DEFAULT_MAX_LENGTH, suffix: str = DEFAULT_SUFFIX) -> str:
    """Truncate *line* to *max_length* characters, appending *suffix* if truncated.

    Args:
        line: The input string to truncate.
        max_length: Maximum allowed length of the returned string (including suffix).
        suffix: String appended when truncation occurs.

    Returns:
        The original line if it fits within *max_length*, otherwise a truncated
        version with *suffix* appended.

    Raises:
        ValueError: If *max_length* is less than or equal to zero.
        ValueError: If *suffix* is longer than *max_length*.
    """
    if max_length <= 0:
        raise ValueError(f"max_length must be positive, got {max_length}")
    if len(suffix) > max_length:
        raise ValueError(
            f"suffix length ({len(suffix)}) exceeds max_length ({max_length})"
        )
    if len(line) <= max_length:
        return line
    cut = max_length - len(suffix)
    return line[:cut] + suffix


def truncate_lines(
    lines: Iterable[str],
    max_length: int = DEFAULT_MAX_LENGTH,
    suffix: str = DEFAULT_SUFFIX,
) -> Iterator[str]:
    """Yield each line from *lines* truncated to *max_length*.

    Args:
        lines: Iterable of log lines.
        max_length: Maximum character length per line.
        suffix: Appended to truncated lines.

    Yields:
        Truncated (or original) lines.
    """
    for line in lines:
        yield truncate_line(line, max_length=max_length, suffix=suffix)


def count_truncated(
    lines: Iterable[str],
    max_length: int = DEFAULT_MAX_LENGTH,
) -> int:
    """Return the number of lines in *lines* that exceed *max_length* characters."""
    return sum(1 for line in lines if len(line) > max_length)
