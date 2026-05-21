"""Tail support: follow a log file as new lines are appended."""

import time
import os
from typing import Iterator, Optional


def tail_file(
    path: str,
    poll_interval: float = 0.2,
    max_wait: Optional[float] = None,
) -> Iterator[str]:
    """Yield new lines appended to *path*, similar to ``tail -f``.

    Parameters
    ----------
    path:
        Path to the log file to follow.
    poll_interval:
        Seconds to sleep between polls when no new data is available.
    max_wait:
        If given, stop after this many seconds of total elapsed time.
        Useful for testing and bounded runs.
    """
    start = time.monotonic()
    with open(path, "r", errors="replace") as fh:
        # Seek to end so we only see new content.
        fh.seek(0, os.SEEK_END)
        while True:
            line = fh.readline()
            if line:
                yield line.rstrip("\n")
            else:
                if max_wait is not None:
                    elapsed = time.monotonic() - start
                    if elapsed >= max_wait:
                        return
                time.sleep(poll_interval)


def tail_lines(
    path: str,
    n: int = 10,
) -> list[str]:
    """Return the last *n* lines of *path* without loading the whole file."""
    if n <= 0:
        return []
    block_size = 8192
    lines: list[str] = []
    with open(path, "rb") as fh:
        fh.seek(0, os.SEEK_END)
        remaining = fh.tell()
        buf = b""
        while remaining > 0 and len(lines) <= n:
            read_size = min(block_size, remaining)
            remaining -= read_size
            fh.seek(remaining)
            chunk = fh.read(read_size)
            buf = chunk + buf
            lines = buf.decode(errors="replace").splitlines()
        return lines[-n:]
