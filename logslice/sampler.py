"""Line sampling utilities for logslice.

Provides reservoir sampling and rate-based sampling to reduce output
volume when working with very large log files.
"""

import random
from typing import Iterable, Iterator


def sample_by_rate(lines: Iterable[str], rate: float) -> Iterator[str]:
    """Yield each line with probability `rate` (0.0 < rate <= 1.0).

    Args:
        lines: Iterable of log lines.
        rate: Fraction of lines to keep, e.g. 0.1 keeps ~10 %.

    Yields:
        Lines selected by random sampling.

    Raises:
        ValueError: If rate is not in the range (0, 1].
    """
    if not (0.0 < rate <= 1.0):
        raise ValueError(f"rate must be in (0, 1], got {rate!r}")
    for line in lines:
        if random.random() < rate:
            yield line


def sample_reservoir(lines: Iterable[str], k: int) -> list[str]:
    """Return a reservoir sample of exactly *k* lines (or fewer if the
    input has fewer than *k* lines).

    Uses Vitter's Algorithm R so the entire iterable is consumed only once
    and no line index is required up front.

    Args:
        lines: Iterable of log lines.
        k: Maximum number of lines to return.

    Returns:
        A list of up to *k* lines chosen uniformly at random.

    Raises:
        ValueError: If k is not a positive integer.
    """
    if k <= 0:
        raise ValueError(f"k must be a positive integer, got {k!r}")

    reservoir: list[str] = []
    for i, line in enumerate(lines):
        if i < k:
            reservoir.append(line)
        else:
            j = random.randint(0, i)
            if j < k:
                reservoir[j] = line
    return reservoir


def sample_every_nth(lines: Iterable[str], n: int) -> Iterator[str]:
    """Yield every *n*-th line (deterministic, 1-based index).

    Args:
        lines: Iterable of log lines.
        n: Step size; must be >= 1.

    Yields:
        Lines at positions 1, n+1, 2n+1, …

    Raises:
        ValueError: If n is less than 1.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n!r}")
    for i, line in enumerate(lines):
        if i % n == 0:
            yield line
