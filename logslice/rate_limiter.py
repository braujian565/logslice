"""Rate limiter for log output — limits lines emitted per second or per time window."""

import time
from collections import deque
from typing import Iterable, Iterator


class RateLimiter:
    """Token-bucket style rate limiter.

    Tracks how many lines have been emitted within a rolling time window
    and drops lines that exceed the configured rate.
    """

    def __init__(self, max_lines: int, window_seconds: float = 1.0) -> None:
        if max_lines <= 0:
            raise ValueError("max_lines must be a positive integer")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self.max_lines = max_lines
        self.window_seconds = window_seconds
        self._timestamps: deque = deque()

    def allow(self, now: float | None = None) -> bool:
        """Return True if a line should be allowed through, False if it should be dropped."""
        ts = now if now is not None else time.monotonic()
        cutoff = ts - self.window_seconds

        # Evict timestamps outside the current window
        while self._timestamps and self._timestamps[0] <= cutoff:
            self._timestamps.popleft()

        if len(self._timestamps) < self.max_lines:
            self._timestamps.append(ts)
            return True
        return False

    def reset(self) -> None:
        """Clear internal state."""
        self._timestamps.clear()


def rate_limit_lines(
    lines: Iterable[str],
    max_lines: int,
    window_seconds: float = 1.0,
    *,
    _clock: float | None = None,
) -> Iterator[str]:
    """Yield lines from *lines* subject to a rate limit.

    Args:
        lines: Input iterable of log lines.
        max_lines: Maximum number of lines allowed per *window_seconds*.
        window_seconds: Length of the rolling time window in seconds.
        _clock: Fixed timestamp used in tests to avoid real-time dependency.

    Yields:
        Lines that pass the rate limit; excess lines are silently dropped.
    """
    limiter = RateLimiter(max_lines=max_lines, window_seconds=window_seconds)
    for line in lines:
        now = _clock if _clock is not None else time.monotonic()
        if limiter.allow(now=now):
            yield line
