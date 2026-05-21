"""Output formatting utilities for logslice."""

import json
from typing import List, Optional, Tuple
from datetime import datetime


def format_line_plain(line: str, line_number: Optional[int] = None) -> str:
    """Return the line as-is, optionally prefixed with line number."""
    if line_number is not None:
        return f"{line_number}:{line}"
    return line


def format_line_json(
    line: str,
    line_number: Optional[int] = None,
    timestamp: Optional[datetime] = None,
) -> str:
    """Return a JSON-encoded representation of a log line."""
    record = {"line": line.rstrip("\n")}
    if line_number is not None:
        record["lineno"] = line_number
    if timestamp is not None:
        record["timestamp"] = timestamp.isoformat()
    return json.dumps(record)


def format_summary(matched: int, total: int, elapsed: Optional[float] = None) -> str:
    """Return a human-readable summary string."""
    parts = [f"Matched {matched} of {total} lines"]
    if elapsed is not None:
        parts.append(f"in {elapsed:.3f}s")
    return " ".join(parts) + "."


def format_lines(
    lines: List[Tuple[int, str]],
    fmt: str = "plain",
    timestamps: Optional[List[Optional[datetime]]] = None,
    show_line_numbers: bool = False,
) -> List[str]:
    """Format a list of (line_number, content) tuples.

    Args:
        lines: List of (1-based line number, raw line string) tuples.
        fmt: One of 'plain' or 'json'.
        timestamps: Optional list of parsed timestamps aligned with *lines*.
        show_line_numbers: Prefix plain output with line numbers.

    Returns:
        List of formatted strings (no trailing newlines).
    """
    if fmt not in ("plain", "json"):
        raise ValueError(f"Unknown format: {fmt!r}. Choose 'plain' or 'json'.")

    result = []
    for idx, (lineno, content) in enumerate(lines):
        ts = timestamps[idx] if timestamps else None
        if fmt == "json":
            result.append(format_line_json(content, lineno if show_line_numbers else None, ts))
        else:
            result.append(format_line_plain(content.rstrip("\n"), lineno if show_line_numbers else None))
    return result
