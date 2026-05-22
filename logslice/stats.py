"""Line-level statistics collector for log streams."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Optional


@dataclass
class LogStats:
    total_lines: int = 0
    matched_lines: int = 0
    bytes_processed: int = 0
    level_counts: Counter = field(default_factory=Counter)
    error_count: int = 0
    warning_count: int = 0

    @property
    def match_rate(self) -> float:
        if self.total_lines == 0:
            return 0.0
        return self.matched_lines / self.total_lines

    def to_dict(self) -> dict:
        return {
            "total_lines": self.total_lines,
            "matched_lines": self.matched_lines,
            "bytes_processed": self.bytes_processed,
            "match_rate": round(self.match_rate, 4),
            "level_counts": dict(self.level_counts),
            "error_count": self.error_count,
            "warning_count": self.warning_count,
        }


_LEVEL_RE = re.compile(
    r"\b(DEBUG|INFO|NOTICE|WARNING|WARN|ERROR|CRITICAL|FATAL)\b", re.IGNORECASE
)


def collect_stats(
    lines: Iterable[str],
    pattern: Optional[re.Pattern] = None,
) -> LogStats:
    """Consume *lines* and return a populated :class:`LogStats`."""
    stats = LogStats()
    for line in lines:
        stats.total_lines += 1
        stats.bytes_processed += len(line.encode())
        if pattern is None or pattern.search(line):
            stats.matched_lines += 1
        m = _LEVEL_RE.search(line)
        if m:
            level = m.group(1).upper()
            if level in ("WARN", "WARNING"):
                level = "WARNING"
            stats.level_counts[level] += 1
            if level == "ERROR":
                stats.error_count += 1
            elif level in ("CRITICAL", "FATAL"):
                stats.error_count += 1
            elif level == "WARNING":
                stats.warning_count += 1
    return stats
