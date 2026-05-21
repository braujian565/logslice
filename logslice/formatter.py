"""Output formatting for log lines and summaries."""

from __future__ import annotations

import json
from typing import Iterable, Iterator, Optional


def format_line_plain(
    line: str,
    line_number: Optional[int] = None,
) -> str:
    """Return a plain-text representation of a log line.

    Args:
        line: The raw log line (trailing newline stripped).
        line_number: Optional 1-based line number to prepend.

    Returns:
        Formatted string ready for output.
    """
    line = line.rstrip("\n")
    if line_number is not None:
        return f"{line_number:>6}: {line}"
    return line


def format_line_json(
    line: str,
    line_number: Optional[int] = None,
    extra: Optional[dict] = None,
) -> str:
    """Return a JSON-encoded representation of a log line.

    Args:
        line: The raw log line.
        line_number: Optional 1-based line number.
        extra: Optional mapping of additional fields to include.

    Returns:
        JSON string.
    """
    payload: dict = {"line": line.rstrip("\n")}
    if line_number is not None:
        payload["n"] = line_number
    if extra:
        payload.update(extra)
    return json.dumps(payload, ensure_ascii=False)


def format_summary(
    total: int,
    matched: int,
    label: str = "matched",
) -> str:
    """Return a human-readable summary line.

    Args:
        total: Total lines processed.
        matched: Lines that passed all filters.
        label: Verb to use in the summary (default: 'matched').

    Returns:
        Summary string.
    """
    pct = (matched / total * 100) if total else 0.0
    return f"{matched}/{total} lines {label} ({pct:.1f}%)"


def format_aggregation(
    aggregated: dict[str, int],
    title: str = "Aggregation",
) -> str:
    """Return a formatted table of aggregation results.

    Args:
        aggregated: Mapping of bucket label -> count.
        title: Header label for the table.

    Returns:
        Multi-line string table.
    """
    if not aggregated:
        return f"{title}\n  (no data)"

    max_key = max(len(k) for k in aggregated)
    max_val = max(len(str(v)) for v in aggregated.values())
    header = f"{title}"
    sep = "-" * (max_key + max_val + 5)
    rows = [header, sep]
    for key, count in aggregated.items():
        rows.append(f"  {key:<{max_key}}  {count:>{max_val}d}")
    return "\n".join(rows)


def format_lines(
    lines: Iterable[str],
    fmt: str = "plain",
    start_number: int = 1,
    show_numbers: bool = False,
) -> Iterator[str]:
    """Yield formatted lines according to the chosen format.

    Args:
        lines: Iterable of raw log lines.
        fmt: Output format — 'plain' or 'json'.
        start_number: Line number for the first line.
        show_numbers: Whether to include line numbers.
    """
    for i, line in enumerate(lines, start=start_number):
        n = i if show_numbers else None
        if fmt == "json":
            yield format_line_json(line, line_number=n)
        else:
            yield format_line_plain(line, line_number=n)
