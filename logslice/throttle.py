"""Line throttling: emit at most N lines per time window, with optional burst support."""

from __future__ import annotations

import time
from collections import deque
from typing import Iterable, Iterator


class Throttle:
    """Token-bucket style throttle: allow at most `max_lines` per `window` seconds."""

    def __init__(self, max_lines: int, window: float = 1.0) -> None:
        if max_lines <= 0:
            raise ValueError("max_lines must be a positive integer")
        if window <= 0:
            raise ValueError("window must be a positive number")
        self.max_lines = max_lines
        self.window = window
        self._timestamps: deque[float] = deque()

    def allow(self, now: float | None = None) -> bool:
        """Return True if a line should be emitted right now."""
        ts = now if now is not None else time.monotonic()
        cutoff = ts - self.window
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()
        if len(self._timestamps) < self.max_lines:
            self._timestamps.append(ts)
            return True
        return False

    def reset(self) -> None:
        """Clear internal state."""
        self._timestamps.clear()


def throttle_lines(
    lines: Iterable[str],
    max_lines: int,
    window: float = 1.0,
    *,
    _throttle: Throttle | None = None,
) -> Iterator[str]:
    """Yield lines from *lines*, dropping those that exceed the rate limit.

    Parameters
    ----------
    lines:     source iterable of log lines
    max_lines: maximum lines to pass through per *window* seconds
    window:    sliding window size in seconds (default 1.0)
    """
    throttle = _throttle if _throttle is not None else Throttle(max_lines, window)
    for line in lines:
        if throttle.allow():
            yield line
