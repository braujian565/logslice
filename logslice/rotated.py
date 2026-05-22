"""Support for reading log files that may have been rotated.

Detects inode changes or truncation to handle logrotate-style rotation.
"""
from __future__ import annotations

import os
from typing import Generator, Optional


def _get_inode(path: str) -> Optional[int]:
    """Return the inode number of *path*, or None if the file does not exist."""
    try:
        return os.stat(path).st_ino
    except FileNotFoundError:
        return None


def _get_size(path: str) -> int:
    """Return the current size of *path* in bytes, or 0 if missing."""
    try:
        return os.stat(path).st_size
    except FileNotFoundError:
        return 0


def read_with_rotation(
    path: str,
    start_offset: int = 0,
    *,
    reopen_delay: float = 0.5,
) -> Generator[tuple[str, int], None, None]:
    """Yield ``(line, offset)`` tuples from *path*, surviving log rotation.

    When a rotation is detected (inode change or file shrinkage) the reader
    reopens the file from the beginning so no lines are skipped.

    Args:
        path: Path to the log file.
        start_offset: Byte offset to seek to before reading (e.g. from a
            checkpoint).  Ignored after a rotation.
        reopen_delay: Not used in the generator itself; exposed so callers can
            document their intended polling cadence.

    Yields:
        Tuples of ``(line_text, new_offset)`` where *new_offset* is the file
        position after the line has been read.
    """
    current_inode = _get_inode(path)
    fh = open(path, "r", errors="replace")
    if start_offset:
        fh.seek(start_offset)

    try:
        while True:
            line = fh.readline()
            if line:
                yield line, fh.tell()
                continue

            # No data — check for rotation.
            new_inode = _get_inode(path)
            new_size = _get_size(path)
            current_pos = fh.tell()

            rotated = (new_inode is not None and new_inode != current_inode) or (
                new_size < current_pos
            )
            if rotated:
                fh.close()
                fh = open(path, "r", errors="replace")
                current_inode = _get_inode(path)
                continue

            # Nothing new and no rotation — caller controls the polling loop.
            return
    finally:
        fh.close()
