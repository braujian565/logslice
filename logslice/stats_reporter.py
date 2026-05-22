"""Format and emit :class:`LogStats` reports."""

from __future__ import annotations

import json
from typing import Literal

from logslice.stats import LogStats

FormatType = Literal["plain", "json"]


def format_stats_plain(stats: LogStats, title: str = "Log Statistics") -> str:
    lines = [
        f"=== {title} ===",
        f"  Total lines     : {stats.total_lines}",
        f"  Matched lines   : {stats.matched_lines}",
        f"  Match rate      : {stats.match_rate:.1%}",
        f"  Bytes processed : {stats.bytes_processed}",
        f"  Errors          : {stats.error_count}",
        f"  Warnings        : {stats.warning_count}",
    ]
    if stats.level_counts:
        lines.append("  Level breakdown :")
        for level, count in sorted(stats.level_counts.items()):
            lines.append(f"    {level:<10} {count}")
    return "\n".join(lines)


def format_stats_json(stats: LogStats) -> str:
    return json.dumps(stats.to_dict(), indent=2)


def report_stats(
    stats: LogStats,
    fmt: FormatType = "plain",
    title: str = "Log Statistics",
) -> str:
    """Return a formatted statistics report string."""
    if fmt == "json":
        return format_stats_json(stats)
    return format_stats_plain(stats, title=title)
