"""Output writer for logslice.

Handles writing processed log lines to files or stdout,
supporting plain text and JSON output formats with optional
compression for file targets.
"""

import gzip
import io
import json
import sys
from pathlib import Path
from typing import Iterable, Optional, TextIO, Union


def _open_output(
    path: Optional[Union[str, Path]],
    compress: bool = False,
) -> TextIO:
    """Open an output stream for writing.

    Args:
        path: Destination file path, or None to use stdout.
        compress: If True and path is given, write gzip-compressed output.

    Returns:
        A writable text-mode file object.
    """
    if path is None:
        return sys.stdout

    path = Path(path)
    if compress:
        # gzip.open returns a binary-mode file; wrap in a text adapter
        binary = gzip.open(path, "wt", encoding="utf-8")
        return binary  # type: ignore[return-value]

    return path.open("w", encoding="utf-8")


def write_lines(
    lines: Iterable[str],
    path: Optional[Union[str, Path]] = None,
    *,
    compress: bool = False,
    add_newline: bool = True,
) -> int:
    """Write an iterable of lines to *path* (or stdout if None).

    Args:
        lines: Iterable of strings to write.
        path: Output file path.  ``None`` writes to stdout.
        compress: Gzip-compress the output (only meaningful with *path*).
        add_newline: Append ``\\n`` to each line that does not already end
            with one.

    Returns:
        The total number of lines written.
    """
    count = 0
    stream = _open_output(path, compress=compress)
    try:
        for line in lines:
            if add_newline and not line.endswith("\n"):
                line = line + "\n"
            stream.write(line)
            count += 1
    finally:
        if stream is not sys.stdout:
            stream.close()
    return count


def write_json_lines(
    records: Iterable[dict],
    path: Optional[Union[str, Path]] = None,
    *,
    compress: bool = False,
    indent: Optional[int] = None,
) -> int:
    """Serialise an iterable of dicts as JSON Lines (one JSON object per line).

    Args:
        records: Iterable of dicts to serialise.
        path: Output file path.  ``None`` writes to stdout.
        compress: Gzip-compress the output (only meaningful with *path*).
        indent: If given, pretty-print each JSON object with this indent level.
            Note that with indentation each record spans multiple lines, so the
            output is no longer strict JSON Lines format.

    Returns:
        The total number of records written.
    """
    count = 0
    stream = _open_output(path, compress=compress)
    try:
        for record in records:
            stream.write(json.dumps(record, indent=indent, ensure_ascii=False))
            stream.write("\n")
            count += 1
    finally:
        if stream is not sys.stdout:
            stream.close()
    return count


def write_to_buffer(
    lines: Iterable[str],
    *,
    add_newline: bool = True,
) -> str:
    """Collect *lines* into an in-memory string (useful for testing).

    Args:
        lines: Iterable of strings.
        add_newline: Append ``\\n`` to lines that don't already end with one.

    Returns:
        A single string containing all lines concatenated.
    """
    buf = io.StringIO()
    for line in lines:
        if add_newline and not line.endswith("\n"):
            line = line + "\n"
        buf.write(line)
    return buf.getvalue()
