"""Line-level summarizer: collapse repeated or similar lines into summary entries."""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional


@dataclass
class SummaryEntry:
    pattern: str
    count: int
    sample: str
    line_numbers: List[int] = field(default_factory=list)

    def __str__(self) -> str:
        return f"[x{self.count}] {self.sample.rstrip()}"


def _normalize(line: str, placeholders: bool = True) -> str:
    """Replace numbers and hex strings with placeholders for grouping."""
    if not placeholders:
        return line.rstrip()
    line = re.sub(r'\b[0-9a-fA-F]{8,}\b', '<HEX>', line)
    line = re.sub(r'\b\d+\.\d+\.\d+\.\d+\b', '<IP>', line)
    line = re.sub(r'\b\d+\b', '<N>', line)
    return line.rstrip()


def summarize_lines(
    lines: Iterable[str],
    *,
    placeholders: bool = True,
    min_count: int = 1,
    max_entries: Optional[int] = None,
) -> List[SummaryEntry]:
    """Group lines by normalized form and return summary entries."""
    groups: dict[str, SummaryEntry] = {}
    for lineno, raw in enumerate(lines, start=1):
        key = _normalize(raw, placeholders=placeholders)
        if key in groups:
            groups[key].count += 1
            groups[key].line_numbers.append(lineno)
        else:
            groups[key] = SummaryEntry(
                pattern=key,
                count=1,
                sample=raw,
                line_numbers=[lineno],
            )
    results = [
        entry for entry in groups.values() if entry.count >= min_count
    ]
    results.sort(key=lambda e: e.count, reverse=True)
    if max_entries is not None:
        results = results[:max_entries]
    return results


def iter_unique_summaries(lines: Iterable[str], *, placeholders: bool = True) -> Iterator[str]:
    """Yield one representative line per unique normalized form."""
    seen: set[str] = set()
    for raw in lines:
        key = _normalize(raw, placeholders=placeholders)
        if key not in seen:
            seen.add(key)
            yield raw


def top_repeated(
    lines: Iterable[str],
    n: int = 10,
    *,
    placeholders: bool = True,
) -> List[SummaryEntry]:
    """Return the top-N most repeated line patterns."""
    return summarize_lines(lines, placeholders=placeholders, min_count=2, max_entries=n)
